# Robust, lean image for RTSP/Webcam inference
FROM python:3.11-slim

ARG DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 \
    OUTPUT_DIR=/app/output LOG_DIR=/app/logs \
    SOURCE=0

WORKDIR /app

# System deps for OpenCV + codecs
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg libglib2.0-0 libsm6 libxext6 libxrender1 \
 && rm -rf /var/lib/apt/lists/*

# Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# App code
COPY app.py .

# Non-root user + dirs
RUN useradd -m -u 1001 appuser \
 && groupadd -f video \
 && usermod -aG video appuser \
 && mkdir -p "${OUTPUT_DIR}" "${LOG_DIR}" \
 && chown -R appuser:appuser /app
USER appuser

# Device-independent healthcheck (checks cascade availability, not camera)
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
  CMD python - <<'PY'\nimport cv2,sys; c=cv2.CascadeClassifier(cv2.data.haarcascades+'haarcascade_frontalface_default.xml'); sys.exit(0 if not c.empty() else 1)\nPY

# Default: pick source from env (webcam index or RTSP URL)
CMD ["bash","-lc","python app.py --rtsp-url ${SOURCE} --save-interval 5"]

