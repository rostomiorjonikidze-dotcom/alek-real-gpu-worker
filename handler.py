"""ALEK REAL Runpod Serverless entrypoint. GPU inference is opt-in and unverified."""
import runpod
from worker import process_job


def handler(job):
    return process_job(job)


# Keep at module level so Runpod repository detection finds the entrypoint.
runpod.serverless.start({"handler": handler})
