import unittest
from unittest.mock import patch
from handler import handler


class TestHandler(unittest.TestCase):
    def test_invalid_prompt(self):
        self.assertEqual(handler({"input": {"prompt": ""}})["error"], "INVALID_PROMPT")

    def test_invalid_duration(self):
        self.assertEqual(handler({"input": {"prompt": "Scene", "duration_seconds": 60}})["error"], "UNSUPPORTED_VIDEO_SETTINGS")

    def test_gpu_disabled_by_default(self):
        with patch.dict("os.environ", {"ALEK_ENABLE_GPU_INFERENCE": "false"}):
            self.assertEqual(handler({"input": {"prompt": "Cinematic scene"}})["error"], "GPU_INFERENCE_DISABLED")


if __name__ == "__main__":
    unittest.main()
