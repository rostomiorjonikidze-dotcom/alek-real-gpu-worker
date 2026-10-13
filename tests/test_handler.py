import unittest
from handler import handler

class TestHandler(unittest.TestCase):
    def test_invalid_prompt(self):
        self.assertEqual(handler({"input":{"prompt":""}})["error"],"INVALID_PROMPT")
    def test_invalid_duration(self):
        self.assertEqual(handler({"input":{"prompt":"Scene","duration_seconds":60}})["error"],"UNSUPPORTED_VIDEO_SETTINGS")
    def test_not_ready(self):
        self.assertEqual(handler({"input":{"prompt":"Cinematic scene"}})["error"],"MODEL_ADAPTER_NOT_READY")

if __name__ == "__main__":
    unittest.main()
