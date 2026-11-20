# ALEK REAL — RunPod Serverless GPU worker

Owner-pilot, **not yet GPU-tested**. Code is designed for an RTX A6000 / A40 48 GB
worker. The Supabase backend and public video.alek.best UI must also be connected
before customers can use real generation.

## What this repository implements

- Wan2.2 TI2V-5B **text-to-video** via Diffusers 0.37.1.
- 5-second or experimental 10-second clips, 24 fps, 16:9 / 9:16 / 1:1.
- CUDA runtime 12.4, with float32 VAE and bfloat16 rest of model.
- CPU offloading and support for RunPod Hugging Face cached-model snapshots.
- Protected, signed upload to the private Supabase `alek-real-renders` bucket.
- Input and upload URL validation before expensive inference.
- Explicit GPU off switch (disabled by default).
- Python unit tests, including mocked end-to-end file handoff.

**Not implemented yet:** image-to-video and public customer charging. Real GPU output,
runtime/VRAM behavior and MP4 delivery remain unverified until a paid smoke test.

## RunPod setup — pick exactly this GitHub repository

1. Serverless > New Endpoint > **Deploy from a GitHub repository**.
2. Repository `rostomiorjonikidze-dotcom/alek-real-gpu-worker`;
   branch `main`, Dockerfile `/Dockerfile`, type **Queue**.
3. GPU: **Previous generation**, select **RTX A6000** or **A40** (48 GB).
   This image is CUDA 12.4 and is **not** for Blackwell.
4. **Max workers: 1; Active workers: 0; GPUs per worker: 1**.
   Keep idle timeout low, use initialization timeout at least **900 sec**,
   execution timeout at least **1800 sec** for testing.
5. **Cached model**: `Wan-AI/Wan2.2-TI2V-5B-Diffusers` (34+ GB).
   RunPod mounts it under `/runpod-volume/huggingface-cache/hub`.
   Without caching, cold starts can download tens of GB while billed.
6. Environment variable: `ALEK_ENABLE_GPU_INFERENCE=false` for build
   and no-cost API connectivity tests. When testing one actual video,
   set this to `true` *only after agreeing to the GPU cost* and checking
   the RunPod balance. The Docker image defaults to false.
   Optional: `ALEK_STORAGE_HOST=aqjpznneffqhpbiydejv.supabase.co`.
7. Click Deploy only after reviewing the GPU price and budget. Building
   the image may incur platform-specific costs; GPU billing starts when
   a worker runs. Do not set an active worker to 1 just to test the build.

## Connecting the Supabase backend

Project: `aqjpznneffqhpbiydejv`.

Existing owner-pilot Edge Function: `alek-real-runpod-gateway`. Add its
secrets through the Supabase Dashboard (never the Git repository):
- `ALEK_RUNPOD_API_KEY`
- `ALEK_RUNPOD_ENDPOINT_ID`
- `ALEK_RUNPOD_MAX_JOB_COST_CENTS` (a conservative per-job ceiling, USD cents)

The server also requires a registered **owner** account in
`public.alek_real_profiles`, and `public.alek_real_budget_settings` must
have `owner_enabled=true`, `gpu_enabled=true`, and positive daily
and monthly caps. Keep these false/0 until a controlled real GPU test.

`ALEK_RUNPOD_MAX_JOB_COST_CENTS` is an *application-side estimate ceiling*,
not an independent spending cap enforced by RunPod. RunPod's actual GPU
billing can exceed estimates if inference is slow. Review RunPod account
budget controls and job timeouts.

## Testing with no GPU charges

```bash
python -m compileall -q handler.py worker.py tests
python -m unittest discover -s tests -v
```

The test suite mocks the model and uploader; it verifies validation and
handoff only. It does **not** guarantee Docker build success or real inference.
RunPod's automatic detector may warn that it cannot see
`runpod.serverless.start()`; the entrypoint is `handler.py` and the call
is present there. Use RunPod's build logs for the authoritative result.

## GPU test: one video only

- First verify endpoint build status is **Completed** and worker logs healthy.
- Owner authenticates to Supabase, creates a 5-second draft, starts one job
  through `alek-real-runpod-gateway`, and polls until complete.
- Verify uploaded MP4 exists in private Supabase Storage and
  download is a short-lived signed URL.
- Record actual execution time, image memory use, total cost, and failure
  handling. If it fails, disable `ALEK_ENABLE_GPU_INFERENCE` again and
  inspect RunPod worker logs. Do not launch overlapping requests.

## Security/cost caveats

- Never paste RunPod/Supabase keys into chat, Vercel public variables or Git.
- The worker rejects external upload domains and redirects.
- Signed upload URLs expire (typically 2 hours). Keep model caching enabled.
- A 10-second 241-frame render may exceed A6000 VRAM/RAM or job timeouts.
  Start with a single 5-second clip.
- This is **owner-only** until billing, idempotency, payment settlement,
  full end-to-end tests and abuse limits have been audited.

Official references:
- https://docs.runpod.io/serverless/workers/github-integration
- https://docs.runpod.io/serverless/endpoints/model-caching
- https://huggingface.co/Wan-AI/Wan2.2-TI2V-5B-Diffusers
- https://supabase.com/docs/reference/javascript/file-buckets-createsigneduploadurl
