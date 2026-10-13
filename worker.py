"""Wan2.2 TI2V prototype. Requires GPU testing before enabling paid traffic."""
import os
import tempfile
from pathlib import Path
from urllib.parse import urlparse

MODEL_ID = "Wan-AI/Wan2.2-TI2V-5B-Diffusers"
RATIOS = {"16:9": (832, 480), "9:16": (480, 832), "1:1": (640, 640)}
_PIPE = None

def validate(payload):
    if not isinstance(payload, dict):
        raise ValueError("INVALID_INPUT")
    prompt = payload.get("prompt")
    if not isinstance(prompt, str) or not 1 <= len(prompt.strip()) <= 3000:
        raise ValueError("INVALID_PROMPT")
    duration = payload.get("duration_seconds", 5)
    ratio = payload.get("aspect_ratio", "16:9")
    if type(duration) is not int or duration not in (5, 10) or ratio not in RATIOS:
        raise ValueError("UNSUPPORTED_VIDEO_SETTINGS")
    seed = payload.get("seed", 42)
    if type(seed) is not int or not 0 <= seed < 2**32:
        raise ValueError("INVALID_SEED")
    return prompt.strip(), duration, ratio, seed

def get_pipeline():
    global _PIPE
    if _PIPE is None:
        import torch
        from diffusers import WanPipeline
        if not torch.cuda.is_available():
            raise RuntimeError("CUDA_UNAVAILABLE")
        pipe = WanPipeline.from_pretrained(MODEL_ID, torch_dtype=torch.bfloat16)
        pipe.enable_model_cpu_offload()
        _PIPE = pipe
    return _PIPE

def process_job(job):
    try:
        prompt, duration, ratio, seed = validate((job or {}).get("input"))
    except ValueError as e:
        return {"error": str(e)}
    if os.getenv("ALEK_ENABLE_GPU_INFERENCE") != "true":
        return {"error": "GPU_INFERENCE_DISABLED"}
    try:
        import torch
        from diffusers.utils import export_to_video
        import requests
        pipe = get_pipeline()
        width, height = RATIOS[ratio]
        fps = 16
        frames = duration * fps + 1
        result = pipe(prompt=prompt, width=width, height=height,
                      num_frames=frames, guidance_scale=5.0,
                      num_inference_steps=30,
                      generator=torch.Generator(device="cpu").manual_seed(seed))
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "render.mp4"
            export_to_video(result.frames[0], str(path), fps=fps)
            # Upload URL must be created by our authenticated backend and scoped to this job.
            upload_url = (job.get("input") or {}).get("upload_url", "")
            parsed = urlparse(upload_url)
            expected_host = os.getenv("ALEK_STORAGE_HOST", "")
            if parsed.scheme != "https" or not expected_host or parsed.hostname != expected_host:
                return {"error": "UPLOAD_URL_NOT_ALLOWED"}
            with path.open("rb") as file:
                response = requests.put(upload_url, data=file,
                    headers={"Content-Type": "video/mp4"}, timeout=300)
            response.raise_for_status()
        return {"ok": True, "duration_seconds": duration, "model": MODEL_ID}
    except Exception as exc:
        # Never return tokens, signed URLs or other exception contents.
        print("ALEK worker failed:", type(exc).__name__)
        return {"error": "GENERATION_FAILED", "type": type(exc).__name__}
