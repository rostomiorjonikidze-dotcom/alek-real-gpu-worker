# ALEK REAL GPU Worker

Private Runpod Serverless **safety scaffold** for ALEK REAL. **Not production-ready:** the model adapter is not implemented or GPU-tested. No videos are generated and no customer credits should be charged.

## Architecture
- Runpod Serverless receives server-to-server jobs from ALEK REAL's Supabase backend.
- First candidate: `Wan-AI/Wan2.2-TI2V-5B-Diffusers`; later adapters for other video models.
- Generated files will be uploaded to private Supabase Storage; signed URLs only.
- Enforce job ownership, spending caps, credit reservations, retries and idempotent completion server-side.

## Before any paid deployment
1. Install the Runpod GitHub App with **Only select repositories** for this repo.
2. Implement and validate actual Wan2.2 inference, CUDA dependencies, licensing, memory and video output on the selected GPU.
3. Build and test a pinned Docker image.
4. Create a Runpod Serverless endpoint with minimum workers **0**, maximum **1**, and budget limits.
5. Configure `ALEK_RUNPOD_API_KEY` and `ALEK_RUNPOD_ENDPOINT_ID` in Supabase Edge Function Secrets; never commit credentials.
6. Verify callback authentication, storage upload, refunds, credit ledger, PayPal settlement, and end-to-end video delivery.

**Do not deploy this scaffold to serve paying customers.**