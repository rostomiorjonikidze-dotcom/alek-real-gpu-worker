import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from worker import MODEL_ID, process_job, validate, validate_upload_url, model_location

USER = "b7b1da22-7659-4c80-9e92-b178d1bfe59f"
JOB = "add6b1a3-29e6-4ba5-83c2-a36249e8d9b8"
URL = ("https://aqjpznneffqhpbiydejv.supabase.co/storage/v1/object/"
       "upload/sign/alek-real-renders/" + USER + "/" + JOB + ".mp4?token=signed123")


class WorkerTests(unittest.TestCase):
    def test_validation(self):
        self.assertEqual(validate({"prompt": "A movie shot"})[:3], ("A movie shot", 5, "16:9"))
        for input_data in ({}, {"prompt": ""}, {"prompt": "x", "duration_seconds": 60},
                           {"prompt": "x", "duration_seconds": True}, {"prompt": "x", "seed": -1},
                           {"prompt": "x", "aspect_ratio": "3:2"}):
            with self.subTest(input_data=input_data), self.assertRaises(ValueError):
                validate(input_data)

    def test_signed_url_must_be_from_owned_bucket(self):
        self.assertEqual(validate_upload_url(URL), URL)
        bad_urls = [
            "http://aqjpznneffqhpbiydejv.supabase.co" + URL.split(".co", 1)[1],
            URL.replace("aqjpznneffqhpbiydejv.supabase.co", "attacker.example"),
            URL.replace("alek-real-renders", "unrelated-bucket"),
            URL.replace("?token=signed123", ""),
            URL.replace(JOB, "../missing"),
            URL.replace("https://", "https://user:password@"),
            URL + "#fragment",
        ]
        for bad in bad_urls:
            with self.subTest(url_kind=bad[:55]), self.assertRaises(ValueError):
                validate_upload_url(bad)

    def test_model_id_and_cache_fallback(self):
        self.assertEqual(MODEL_ID, "Wan-AI/Wan2.2-TI2V-5B-Diffusers")
        with patch.dict(os.environ, {"ALEK_ALLOW_MODEL_DOWNLOAD": "false"}):
            with patch("worker.Path.is_dir", return_value=False):
                with self.assertRaisesRegex(RuntimeError, "MODEL_CACHE_REQUIRED"):
                    model_location()
        with patch.dict(os.environ, {"ALEK_ALLOW_MODEL_DOWNLOAD": "true"}):
            with patch("worker.Path.is_dir", return_value=False):
                self.assertEqual(model_location(), MODEL_ID)

    def test_disabled_never_renders(self):
        payload = {"input": {"prompt": "A film scene", "upload_url": URL}}
        with patch.dict(os.environ, {"ALEK_ENABLE_GPU_INFERENCE": "false"}):
            with patch("worker.render") as mocked:
                self.assertEqual(process_job(payload)["error"], "GPU_INFERENCE_DISABLED")
                mocked.assert_not_called()

    def test_invalid_url_never_renders(self):
        payload = {"input": {"prompt": "A film scene", "upload_url": "https://evil.test"}}
        with patch.dict(os.environ, {"ALEK_ENABLE_GPU_INFERENCE": "true"}):
            with patch("worker.render") as mocked:
                self.assertEqual(process_job(payload)["error"], "UPLOAD_URL_NOT_ALLOWED")
                mocked.assert_not_called()

    def test_fake_render_then_fake_upload(self):
        def fake_render(prompt, duration, ratio, seed, output):
            self.assertEqual(prompt, "A film scene")
            self.assertEqual(duration, 5)
            Path(output).write_bytes(b"0" * 2048)

        with patch.dict(os.environ, {"ALEK_ENABLE_GPU_INFERENCE": "true"}):
            with patch("worker.render", side_effect=fake_render), patch("worker.upload_video") as uploaded:
                result = process_job({"input": {"prompt": "A film scene", "upload_url": URL}})
                self.assertEqual(result["ok"], True)
                self.assertEqual(result["bytes"], 2048)
                self.assertEqual(result["format"], "mp4")
                uploaded.assert_called_once()
                self.assertEqual(uploaded.call_args.args[1], URL)

    def test_missing_render_is_rejected(self):
        with patch.dict(os.environ, {"ALEK_ENABLE_GPU_INFERENCE": "true"}):
            with patch("worker.render", return_value=None), patch("worker.upload_video") as uploaded:
                result = process_job({"input": {"prompt": "A film scene", "upload_url": URL}})
                self.assertEqual(result["error"], "GENERATION_FAILED")
                uploaded.assert_not_called()


if __name__ == "__main__":
    unittest.main()
