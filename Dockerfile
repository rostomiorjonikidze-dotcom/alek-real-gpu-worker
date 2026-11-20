# RTX A6000 / A40 (Ampere): supported CUDA 12.4 runtime.
# Use RunPod "Previous generation" 48GB. New Blackwell GPUs need CUDA 12.8+.
FROM pytorch/pytorch:2.6.0-cuda12.4-cudnn9-runtime
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HOME=/root/.cache/huggingface
RUN apt-get update && apt-get install -y --no-install-recommends \
        ffmpeg ca-certificates \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt /app/requirements.txt
RUN python -m pip install --disable-pip-version-check -r /app/requirements.txt
COPY handler.py worker.py /app/
# Deliberately disabled until owner opts in from RunPod endpoint variables.
ENV ALEK_ENABLE_GPU_INFERENCE=false
CMD ["python", "-u", "handler.py"]
