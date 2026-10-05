# syntax=docker/dockerfile:1
#
# OrthoAssist AI — backend image.
#
# Two-stage build:
#   1. "builder" installs build tools + every Python dependency into a
#      venv — this stage's ~2GB of compilers/caches never ends up in the
#      final image.
#   2. the runtime stage copies ONLY that venv plus the app source, on a
#      fresh slim base. This keeps the shipped image meaningfully smaller
#      and means build-time CVEs (gcc, etc.) aren't sitting in what you
#      actually deploy.
#
# Build:  docker build -t orthoassist-backend ./backend
# Run:    docker run -p 8000:8000 --env-file .env orthoassist-backend

FROM python:3.11-slim AS builder

# Build-time system deps: a compiler toolchain (some ML wheels still need
# one even when a prebuilt wheel exists for most of the stack) and the dev
# headers OpenCV's wheel expects at install time.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .

# CPU-only PyTorch explicitly: PyPI's default `torch`/`torchvision` wheels
# pull in several GB of bundled CUDA libraries, which is both unnecessary
# (no GPU on Render, a typical k8s node pool, etc.) and dramatically slows
# every build/deploy. --extra-index-url (not --index-url) keeps PyPI as the
# source for every other package in requirements.txt, torch/torchvision
# included — pip just prefers the CPU-only build offered by this extra
# index for those two specifically.
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
        --extra-index-url https://download.pytorch.org/whl/cpu \
        -r requirements.txt


FROM python:3.11-slim AS runtime

# Runtime system deps actually needed by opencv-python + mediapipe +
# reportlab/matplotlib at import/run time in a headless container (no
# display, no GPU):
#   libgl1, libglib2.0-0        — OpenCV's GUI-capable build still imports
#                                  these even though we never open a window
#   libsm6, libxext6, libxrender1 — legacy X11 libs some OpenCV/Qt codepaths
#                                  still probe for at import time
#   ffmpeg                      — video decoding for uploaded gait videos
#                                  (OpenCV's VideoCapture needs real codec
#                                  support, not just the Python package)
#   curl                        — used by the HEALTHCHECK below
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    ffmpeg \
    curl \
    
    && rm -rf /var/lib/apt/lists/*

# Run as a non-root user — standard container hardening, and required
# outright by some platforms (including typical Kubernetes
# PodSecurityStandards "restricted" profiles).
RUN useradd --create-home --uid 1000 appuser

COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app
COPY . .

# UPLOAD_DIR default ("uploads", i.e. /app/uploads here) is fine for a
# single-container demo run but is NOT persistent across redeploys/pod
# restarts — see the Kubernetes PersistentVolumeClaim / Render persistent
# disk in the deployment guide, which both mount a real volume at this
# same env var instead.
RUN mkdir -p uploads/xrays uploads/videos && chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

# Both Render and Kubernetes can use this directly (Render: "Docker health
# check path" = /health; Kubernetes: liveness/readinessProbe httpGet on the
# same path — see k8s/backend-deployment.yaml).
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Runs pending Alembic migrations, THEN starts the server — this is what
# makes "change a model, redeploy" actually apply the schema change instead
# of silently doing nothing (create_all() in main.py only ever adds brand
# new tables, never alters existing ones).
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
