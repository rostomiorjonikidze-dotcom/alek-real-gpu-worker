"""ALEK REAL Runpod worker scaffold: intentionally refuses unimplemented inference."""
import runpod

MAX_PROMPT_CHARS = 3000
ALLOWED_DURATIONS = {5, 10}
ALLOWED_RATIOS = {"16:9", "9:16", "1:1"}


def handler(job):
    payload = job.get("input") or {}
    if not isinstance(payload, dict):
        return {"error": "INVALID_INPUT"}
    prompt = payload.get("prompt")
    duration = payload.get("duration_seconds", 5)
    ratio = payload.get("aspect_ratio", "16:9")
    if not isinstance(prompt, str) or not 1 <= len(prompt.strip()) <= MAX_PROMPT_CHARS:
        return {"error": "INVALID_PROMPT"}
    if type(duration) is not int or duration not in ALLOWED_DURATIONS or ratio not in ALLOWED_RATIOS:
        return {"error": "UNSUPPORTED_VIDEO_SETTINGS"}
    return {"error": "MODEL_ADAPTER_NOT_READY", "message": "No GPU inference adapter is deployed; no video was generated."}


if __name__ == "__main__":
    runpod.serverless.start({"handler": handler})
