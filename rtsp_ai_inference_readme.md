# RTSP AI Inference Pipeline 🚀

A lightweight starter project that:
- Connects to **RTSP streams or local webcam**  
- Runs **face detection** using OpenCV Haar cascades  
- Saves annotated frames to `output/` and logs to `logs/`  
- Dockerized with healthcheck  
- Integrated **CI/CD with GitHub Actions** (lint → build → push → simulate deploy)  
- Publishes image to **Docker Hub**  

---

## 📌 Architecture Flow

```
[ RTSP/Webcam ] --> [ Python OpenCV App ] --> [ Annotated Frames in /output ]
                                  |
                             [ Logs in /logs ]
                                  |
                             [ Docker Image ]
                                  |
                      [ GitHub Actions CI/CD Pipeline ]
                            lint → build → push
```

---

## ⚙️ Setup & Run

### Local (Python venv)
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Run with webcam
python app.py --rtsp-url 0 --save-interval 5

# Run with RTSP URL
python app.py --rtsp-url "rtsp://username:password@ip:554/Streaming/Channels/101"
```

### Docker
```bash
# Build image
docker build -t rtsp-ai-inference:local .

# Run container
docker run --rm -it \
  -e OUTPUT_DIR=/app/output -e LOG_DIR=/app/logs \
  -v $(pwd)/output:/app/output -v $(pwd)/logs:/app/logs \
  rtsp-ai-inference:local
```

### Docker Hub (Prebuilt Image)
The image is available on Docker Hub:  
👉 [piyushsharma96/rtsp-ai-inference](https://hub.docker.com/r/piyushsharma96/rtsp-ai-inference)

```bash
# Pull image
docker pull piyushsharma96/rtsp-ai-inference:latest

# Run health check
docker run --rm piyushsharma96/rtsp-ai-inference:latest python app.py --health-check
```

---

## 🐳 Docker Compose
```bash
docker compose up --build
```

---

## 🔎 Health Check
```bash
python app.py --health-check --rtsp-url 0
```

---

## ⚡ CI/CD with GitHub Actions

### Workflow Stages
1. **Lint**  
   - Runs flake8, black, isort checks.  

2. **Security Scan**  
   - Runs `bandit` and `safety` to check vulnerabilities.  

3. **Build & Test**  
   - Builds Docker image with Buildx  
   - Runs health-check (device-independent)  
   - Uploads test logs as artifacts  

4. **Push (main branch only)**  
   - Pushes image to Docker Hub with tags:  
     - `latest` (default branch)  
     - `main` (branch tag)  
     - commit SHA (`9414a90`, etc.)  

5. **Simulated Deployment**  
   - Pulls image from Docker Hub  
   - Runs health-check without needing webcam device  

---

## 📜 Logs & Proof

### Sample Logs
```
2025-08-22 22:07:35,454 INFO Connected to source: 0
2025-08-22 22:07:40,515 INFO frame=1 faces=0 infer_ms=4877.61
2025-08-22 22:07:40,526 INFO Saved annotated frame to output/frame_20250822_163740_516375.jpg
```

### CI/CD Success (GitHub Actions)
✅ Lint passed  
✅ Build & Push to Docker Hub  
✅ Simulated Deploy succeeded (health-check OK)  

_Screenshot proofs are added in `/docs/screenshots/`_  

---

## 📝 Notes
- Uses `opencv-python-headless` to keep image size smaller.  
- If multiple webcams are attached, use `--rtsp-url 1` or `--rtsp-url 2`.  
- RTSP camera streams require username/password in URL.  

---

## 📦 Docker Hub Image

[![Docker Pulls](https://img.shields.io/docker/pulls/piyushsharma96/rtsp-ai-inference?logo=docker)](https://hub.docker.com/r/piyushsharma96/rtsp-ai-inference)

Pull with:
```bash
docker pull piyushsharma96/rtsp-ai-inference:latest
```

---

## 🚧 Challenges & Decisions
- **Problem:** GitHub Actions runners don’t have webcams → health-check was failing.  
- **Fix:** Replaced device-dependent test with Haarcascade cascade check (device-independent).  
- **Decision:** CI/CD pipeline kept **minimal** for clarity but includes linting, security scan, build, push, deploy simulation.  

---

✍️ Maintainer: **Piyush Sharma (Bhaiyaji)**  

