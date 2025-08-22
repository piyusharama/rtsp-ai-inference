# RTSP AI Inference Pipeline (Fixed Starter)
A minimal, working starter that fulfils the assignment:
- Connect to RTSP/webcam
- Face detection using OpenCV Haar cascade
- Save annotated frames to `output/`
- Dockerized with healthcheck
- CI (GitHub Actions) to lint, build, and optionally push

## Architecture
```
[ RTSP/Webcam ] -> [ Python OpenCV App ] -> [ Annotated Frames in /output ]
                              |
                         [ Logs in /logs ]
                              |
                         [ Docker Image ]
                              |
                      [ CI: lint + build(+push) ]
```

## Run (Local)
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python app.py --rtsp-url 0 --save-interval 5
# Use an RTSP URL:
# python app.py --rtsp-url "rtsp://username:password@ip:554/Streaming/Channels/101"
```

## Docker
```bash
docker build -t rtsp-ai-inference:local .
docker run --rm -it \
  -e OUTPUT_DIR=/app/output -e LOG_DIR=/app/logs \
  -v $(pwd)/output:/app/output -v $(pwd)/logs:/app/logs \
  rtsp-ai-inference:local
```

## Docker Compose
```bash
docker compose up --build
```

## Health Check (manual)
```bash
python app.py --health-check --rtsp-url 0
```

## CI/CD (GitHub Actions)
- Create Docker Hub repo and add secrets in GitHub repo:
  - `DOCKERHUB_USERNAME`
  - `DOCKERHUB_TOKEN`
- On push to `main`/`develop`, workflow lints and builds.
- If secrets present, it pushes the image to Docker Hub.

## Logs & Output
- Logs: `logs/app.log` and stdout
- Frames: `output/frame_<UTC_TIMESTAMP>.jpg`

## Notes
- `opencv-python-headless` used to keep the image light.
- For some RTSP cameras, set `--rtsp-url` to the full URL with credentials.
- If your webcam is at index 1 or 2, change `--rtsp-url` accordingly.
```
