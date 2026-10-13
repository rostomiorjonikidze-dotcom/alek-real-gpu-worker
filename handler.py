"""ALEK REAL: Runpod Serverless entrypoint. Safe validation-only until GPU adapter is tested."""
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
    return {"error": "MODEL_ADAPTER_NOT_READY", "message": "GPU inference is not yet enabled; no video was generated."}


# Keep the explicit call visible to Runpod's static repository scanner.
runpod.serverless.start({"handler": handler})
