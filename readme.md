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
                            lint → build → push → deploy
```

---

## ⚙️ Step-by-Step Guide to Run

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/piyushsharma96/rtsp-ai-inference.git
cd rtsp-ai-inference
```

### 2️⃣ Run Locally with Python
```bash
# Create and activate virtual environment
python -m venv .venv && source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run with webcam (index 0)
python app.py --rtsp-url 0 --save-interval 5

# Run with RTSP camera
python app.py --rtsp-url "rtsp://username:password@ip:554/Streaming/Channels/101"
```

### 3️⃣ Run with Docker
```bash
# Build Docker image
docker build -t rtsp-ai-inference:local .

# Run container with mounted logs & outputs
docker run --rm -it \
  --device /dev/video0:/dev/video0 \
  --group-add $(getent group video | cut -d: -f3) \
  -e OUTPUT_DIR=/app/output -e LOG_DIR=/app/logs \
  -v $(pwd)/output:/app/output -v $(pwd)/logs:/app/logs \
  rtsp-ai-inference:local
```

### 4️⃣ Use Prebuilt Docker Hub Image
Image is available on Docker Hub:  
👉 [piyushsharma96/rtsp-ai-inference](https://hub.docker.com/r/piyushsharma96/rtsp-ai-inference)

```bash
# Pull image from Docker Hub
docker pull piyushsharma96/rtsp-ai-inference:latest

# Run health check
docker run --rm piyushsharma96/rtsp-ai-inference:latest python app.py --health-check
```

### 5️⃣ Run with Docker Compose
```bash
docker compose up --build
```

### 6️⃣ Health Check (Manual)
```bash
python app.py --health-check --rtsp-url 0
```

---

## ⚡ CI/CD with GitHub Actions

### Workflow Stages
1. **Lint** → flake8, black, isort checks  
2. **Security Scan** → bandit + safety  
3. **Build & Test** → Docker image build, health-check, upload logs  
4. **Push (main branch only)** → Pushes to Docker Hub (`latest`, `main`, commit SHA)  
5. **Simulated Deploy** → Pulls from Docker Hub and runs health-check  

---

## 📜 Logs & Proof

### Sample Logs
```
2025-08-22 22:07:35,454 INFO Connected to source: 0
2025-08-22 22:07:40,515 INFO frame=1 faces=0 infer_ms=4877.61
2025-08-22 22:07:40,526 INFO Saved annotated frame to output/frame_20250822_163740_516375.jpg
```

### CI/CD Success
✅ Lint passed  
✅ Build & Push to Docker Hub  
✅ Simulated Deploy succeeded (health-check OK)  

_Screenshot proofs are added in `/docs/screenshots/`_  

---

## 📝 Notes
- Uses `opencv-python-headless` for smaller Docker images.  
- If multiple webcams exist, change index (`--rtsp-url 1`, `--rtsp-url 2`).  
- RTSP cameras need credentials in URL.  

---

## 📦 Docker Hub Image

[![Docker Pulls](https://img.shields.io/docker/pulls/piyushsharma96/rtsp-ai-inference?logo=docker)](https://hub.docker.com/r/piyushsharma96/rtsp-ai-inference)

Pull with:
```bash
docker pull piyushsharma96/rtsp-ai-inference:latest
```

---

## 🚧 Challenges & Decisions
- **Problem:** CI runners don’t have webcams → health-check was failing.  
- **Fix:** Used device-independent Haarcascade check for CI.  
- **Decision:** Pipeline kept **minimal & clear** but still includes linting, scanning, build, push, and deploy simulation.  

---

✍️ Maintainer: **Piyush P Sharma**

