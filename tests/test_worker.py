import unittest
from worker import process_job, validate

class WorkerTests(unittest.TestCase):
    def test_validation(self):
        self.assertEqual(validate({"prompt": "A movie shot"})[:3], ("A movie shot", 5, "16:9"))
        with self.assertRaises(ValueError):
            validate({"prompt": ""})
        with self.assertRaises(ValueError):
            validate({"prompt": "x", "duration_seconds": 60})
    def test_disabled_no_gpu(self):
        self.assertEqual(process_job({"input": {"prompt": "A film scene"}})["error"], "GPU_INFERENCE_DISABLED")

if __name__ == "__main__":
    unittest.main()
