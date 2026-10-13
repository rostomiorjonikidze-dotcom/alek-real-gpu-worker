"""ALEK REAL Runpod Serverless entrypoint. GPU inference is opt-in and unverified."""
import os
import runpod
from worker import process_job

def handler(job):
    return process_job(job)

if __name__ == "__main__":
    runpod.serverless.start({"handler": handler})
