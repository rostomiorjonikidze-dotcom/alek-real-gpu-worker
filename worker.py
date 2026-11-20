"""ALEK REAL RunPod Serverless Wan 2.2 text-to-video worker.

No GPU work occurs until ALEK_ENABLE_GPU_INFERENCE=true is explicitly set.
The caller must provide a short-lived, job-scoped Supabase signed upload URL.
"""
import logging
import os
import tempfile
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

MODEL_ID = "Wan-AI/Wan2.2-TI2V-5B-Diffusers"
BUCKET = "alek-real-renders"
RATIOS = {"16:9": (832, 480), "9:16": (480, 832), "1:1": (640, 640)}
FPS = 24
MAX_PROMPT = 3000
_PIPE = None
LOG = logging.getLogger("alek_real.worker")


def validate(payload):
    """Check user-controlled input before downloading any model or using a GPU."""
    if not isinstance(payload, dict):
        raise ValueError("INVALID_INPUT")
    prompt = payload.get("prompt")
    if not isinstance(prompt, str) or not 1 <= len(prompt.strip()) <= MAX_PROMPT:
        raise ValueError("INVALID_PROMPT")
    duration = payload.get("duration_seconds", 5)
    ratio = payload.get("aspect_ratio", "16:9")
    if type(duration) is not int or duration not in (5, 10) or ratio not in RATIOS:
        raise ValueError("UNSUPPORTED_VIDEO_SETTINGS")
    seed = payload.get("seed", 42)
    if type(seed) is not int or not 0 <= seed < 2**32:
        raise ValueError("INVALID_SEED")
    return prompt.strip(), duration, ratio, seed


def validate_upload_url(raw):
    """Reject arbitrary URLs, credentials, redirects and cross-project writes."""
    from uuid import UUID

    if not isinstance(raw, str) or len(raw) > 4096:
        raise ValueError("UPLOAD_URL_NOT_ALLOWED")
    parsed = urlsplit(raw)
    host = os.environ.get("ALEK_STORAGE_HOST", "aqjpznneffqhpbiydejv.supabase.co")
    expected_prefix = "/storage/v1/object/upload/sign/" + BUCKET + "/"
    if (parsed.scheme != "https" or parsed.hostname != host or parsed.port not in (None, 443)
            or parsed.username or parsed.password or parsed.fragment
            or not parsed.path.startswith(expected_prefix)):
        raise ValueError("UPLOAD_URL_NOT_ALLOWED")
    remainder = parsed.path[len(expected_prefix):].split("/")
    if len(remainder) != 2 or not remainder[1].endswith(".mp4"):
        raise ValueError("UPLOAD_URL_NOT_ALLOWED")
    try:
        UUID(remainder[0])
        UUID(remainder[1][:-4])
    except (ValueError, AttributeError):
        raise ValueError("UPLOAD_URL_NOT_ALLOWED") from None
    query = parse_qs(parsed.query, keep_blank_values=True)
    if not query.get("token") or not query["token"][0]:
        raise ValueError("UPLOAD_URL_NOT_ALLOWED")
    return raw


def model_location():
    """Prefer RunPod's host-side Hugging Face cache to avoid billed model download."""
    base = Path("/runpod-volume/huggingface-cache/hub")
    snapshots = base / ("models--" + MODEL_ID.replace("/", "--")) / "snapshots"
    if snapshots.is_dir():
        for path in sorted(snapshots.iterdir(), reverse=True):
            if path.is_dir() and (path / "model_index.json").is_file():
                return str(path)
    if os.environ.get("ALEK_ALLOW_MODEL_DOWNLOAD", "false").lower() == "true":
        return MODEL_ID
    raise RuntimeError("MODEL_CACHE_REQUIRED")


def get_pipeline():
    """Load Wan with bfloat16 transformer and float32 VAE, offloading to host RAM."""
    global _PIPE
    if _PIPE is None:
        import torch
        from diffusers import AutoencoderKLWan, WanPipeline

        if not torch.cuda.is_available():
            raise RuntimeError("CUDA_UNAVAILABLE")
        location = model_location()
        LOG.info("Loading Wan pipeline (cached=%s)", location != MODEL_ID)
        vae = AutoencoderKLWan.from_pretrained(
            location, subfolder="vae", torch_dtype=torch.float32
        )
        pipe = WanPipeline.from_pretrained(
            location, vae=vae, torch_dtype=torch.bfloat16
        )
        # Keep 48GB GPU headroom. CPU RAM is required for model offloading.
        pipe.enable_model_cpu_offload()
        _PIPE = pipe
    return _PIPE


def render(prompt, duration, ratio, seed, destination):
    """Generate a video. Inject/mocking this function needs no CUDA."""
    import torch
    from diffusers.utils import export_to_video

    width, height = RATIOS[ratio]
    result = get_pipeline()(
        prompt=prompt,
        width=width,
        height=height,
        num_frames=duration * FPS + 1,
        guidance_scale=5.0,
        num_inference_steps=30,
        generator=torch.Generator(device="cpu").manual_seed(seed),
    )
    export_to_video(result.frames[0], str(destination), fps=FPS)


def upload_video(destination, signed_url):
    """Stream MP4 to the exact signed path; never follow a redirect."""
    import requests

    with destination.open("rb") as fh:
        response = requests.put(
            signed_url,
            data=fh,
            headers={"Content-Type": "video/mp4"},
            allow_redirects=False,
            timeout=(15, 300),
        )
    if response.status_code not in (200, 201):
        raise RuntimeError("SIGNED_UPLOAD_FAILED")


def process_job(job):
    payload = (job or {}).get("input") if isinstance(job, dict) else None
    try:
        prompt, duration, ratio, seed = validate(payload)
        upload_url = validate_upload_url(payload.get("upload_url"))
    except (ValueError, TypeError) as exc:
        return {"ok": False, "error": str(exc)}

    if os.getenv("ALEK_ENABLE_GPU_INFERENCE", "false").lower() != "true":
        return {"ok": False, "error": "GPU_INFERENCE_DISABLED"}

    try:
        with tempfile.TemporaryDirectory(prefix="alek-render-") as tmp:
            output = Path(tmp) / "render.mp4"
            render(prompt, duration, ratio, seed, output)
            if not output.is_file() or output.stat().st_size < 1024:
                raise RuntimeError("EMPTY_VIDEO")
            byte_count = output.stat().st_size
            upload_video(output, upload_url)
        # Never return signed URLs, API keys, tokens or raw exception strings.
        return {
            "ok": True, "model": MODEL_ID,
            "duration_seconds": duration, "fps": FPS,
            "bytes": byte_count, "format": "mp4",
        }
    except Exception as exc:
        LOG.error("Generation failed: %s", type(exc).__name__)
        return {"ok": False, "error": "GENERATION_FAILED", "type": type(exc).__name__}
