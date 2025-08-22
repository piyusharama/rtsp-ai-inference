#!/usr/bin/env python3
"""
RTSP/WEBcam AI Inference (Robust Face Detect)
- RTSP ya webcam se connect
- Low-light friendly preprocessing (brighten + equalize + optional CLAHE)
- Tunable Haar-cascade params (scaleFactor/minNeighbors/minSize)
- Optional profile-face cascade (side pose)
- Annotated frames save to OUTPUT_DIR
- Structured logging + health-check
"""

import argparse
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import cv2

# ---------- Paths ----------
LOG_DIR = Path(os.getenv("LOG_DIR", "logs"))
OUT_DIR = Path(os.getenv("OUTPUT_DIR", "output"))
LOG_DIR.mkdir(parents=True, exist_ok=True)
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ---------- Logging ----------
logger = logging.getLogger("rtsp_ai_inference")
logger.setLevel(logging.INFO)
_fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
_sh = logging.StreamHandler(sys.stdout); _sh.setFormatter(_fmt)
_fh = logging.FileHandler(LOG_DIR / "app.log"); _fh.setFormatter(_fmt)
if not logger.handlers:
    logger.addHandler(_sh); logger.addHandler(_fh)

# ---------- Video ----------
def open_capture(src, width=None, height=None, fps=None):
    cap = cv2.VideoCapture(src)
    if not cap.isOpened():
        return None
    if width:
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, int(width))
    if height:
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, int(height))
    if fps:
        cap.set(cv2.CAP_PROP_FPS, int(fps))
    return cap

# ---------- Preprocessing ----------
def preprocess_for_faces(frame, alpha=1.5, beta=30, use_clahe=False, equalize=True):
    """
    alpha -> contrast, beta -> brightness
    equalize -> histogram equalization on Y channel
    use_clahe -> stronger local contrast enhancement for low light
    """
    # Brighten/contrast
    frame_b = cv2.convertScaleAbs(frame, alpha=alpha, beta=beta)

    # Y channel equalization
    if equalize or use_clahe:
        yuv = cv2.cvtColor(frame_b, cv2.COLOR_BGR2YUV)
        y = yuv[..., 0]
        if use_clahe:
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            y = clahe.apply(y)
        else:
            y = cv2.equalizeHist(y)
        yuv[..., 0] = y
        frame_b = cv2.cvtColor(yuv, cv2.COLOR_YUV2BGR)

    gray = cv2.cvtColor(frame_b, cv2.COLOR_BGR2GRAY)
    return gray, frame_b  # gray for detection, frame_b for drawing

# ---------- Detection ----------
def load_detectors(use_profile=False):
    base = cv2.data.haarcascades
    frontal_path = base + "haarcascade_frontalface_default.xml"
    frontal = cv2.CascadeClassifier(frontal_path)
    if frontal.empty():
        logger.error("Failed to load frontal cascade: %s", frontal_path)
        return None, None

    profile = None
    if use_profile:
        prof_path = base + "haarcascade_profileface.xml"
        profile = cv2.CascadeClassifier(prof_path)
        if profile.empty():
            logger.warning("Profile-face cascade not found at %s (continuing without it).", prof_path)
            profile = None

    return frontal, profile

def detect_faces(gray, frontal, profile, scale_factor, min_neighbors, min_size):
    faces = frontal.detectMultiScale(
        gray,
        scaleFactor=scale_factor,
        minNeighbors=min_neighbors,
        minSize=(min_size, min_size),
    )

    # Optional: try profile detector for side faces
    if profile is not None:
        faces_prof = profile.detectMultiScale(
            gray,
            scaleFactor=max(1.05, scale_factor),
            minNeighbors=max(3, min_neighbors - 1),
            minSize=(min_size, min_size),
        )
        if len(faces_prof) > 0:
            faces = list(faces) + list(faces_prof)

    return faces

def annotate(frame, faces, color=(0, 255, 0), thickness=2):
    for (x, y, w, h) in faces:
        cv2.rectangle(frame, (x, y), (x + w, y + h), color, thickness)
    return frame

# ---------- Health Check ----------
def health_check(src):
    cap = open_capture(src)
    if cap is None:
        logger.error("Health check failed: cannot open source %s", src)
        return 1
    ok, frame = cap.read()
    cap.release()
    if not ok or frame is None:
        logger.error("Health check failed: cannot read a frame")
        return 2
    logger.info("Health check OK")
    return 0

# ---------- Main Loop ----------
def main():
    p = argparse.ArgumentParser("RTSP/WEBCAM Face Inference")
    p.add_argument("--rtsp-url", type=str, default="0", help="RTSP URL or webcam index (e.g., 0)")
    p.add_argument("--save-interval", type=float, default=5.0, help="Seconds between saving annotated frames")
    p.add_argument("--max-frames", type=int, default=0, help="Stop after N frames (0 = run forever)")
    p.add_argument("--health-check", action="store_true", help="Run health check and exit")

    # Robustness in low light / distance
    p.add_argument("--scale-factor", type=float, default=1.05, help="Haar scaleFactor (lower finds more)")
    p.add_argument("--min-neighbors", type=int, default=3, help="Haar minNeighbors (lower finds more, more FP)")
    p.add_argument("--min-size", type=int, default=20, help="Minimum face size (pixels)")

    # Preprocessing knobs
    p.add_argument("--brighten-alpha", type=float, default=1.6, help="Contrast gain (1.0 = no change)")
    p.add_argument("--brighten-beta", type=int, default=35, help="Brightness offset (0 = no change)")
    p.add_argument("--clahe", action="store_true", help="Use CLAHE (strong local contrast boost)")

    # Video properties (optional)
    p.add_argument("--width", type=int, default=0, help="Capture width (0 = default)")
    p.add_argument("--height", type=int, default=0, help="Capture height (0 = default)")
    p.add_argument("--fps", type=int, default=0, help="Capture FPS (0 = default)")

    # Extra detector
    p.add_argument("--use-profile", action="store_true", help="Also use profile-face cascade (side faces)")

    args = p.parse_args()

    # argparse stores "--rtsp-url" as rtsp_url (underscore). Normalize:
    src = getattr(args, "rtsp_url", "0")
    # If it's a digit string, cast to int for webcam index
    src_cast = int(src) if isinstance(src, str) and src.isdigit() else src

    if args.health_check:
        return health_check(src_cast)

    frontal, profile = load_detectors(use_profile=args.use_profile)
    if frontal is None:
        return 3

    cap = open_capture(src_cast, width=args.width or None, height=args.height or None, fps=args.fps or None)
    if cap is None:
        logger.error("Failed to open source: %s", src)
        return 4

    logger.info("Connected to source: %s", src)
    last_save = 0.0
    saved = 0
    frames = 0
    t_fps = time.time()
    fps_counter = 0

    try:
        while True:
            ok, frame = cap.read()
            if not ok or frame is None:
                logger.warning("Dropped/invalid frame")
                time.sleep(0.2)
                continue

            t0 = time.time()
            gray, disp = preprocess_for_faces(
                frame,
                alpha=args.brighten_alpha,
                beta=args.brighten_beta,
                use_clahe=args.clahe,
                equalize=True,
            )
            faces = detect_faces(
                gray,
                frontal=frontal,
                profile=profile,
                scale_factor=args.scale_factor,
                min_neighbors=args.min_neighbors,
                min_size=args.min_size,
            )
            annotated = annotate(disp, faces)

            infer_ms = (time.time() - t0) * 1000.0
            frames += 1
            fps_counter += 1

            # Simple FPS calc
            now = time.time()
            if now - t_fps >= 1.0:
                logger.info("FPS=%.2f", fps_counter / (now - t_fps))
                t_fps = now
                fps_counter = 0

            logger.info(
                "frame=%d faces=%d infer_ms=%.2f",
                frames,
                0 if faces is None else len(faces),
                infer_ms,
            )

            # Save annotated frames at interval
            if now - last_save >= args.save_interval:
                ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
                out_path = OUT_DIR / f"frame_{ts}.jpg"
                cv2.imwrite(str(out_path), annotated)
                saved += 1
                last_save = now
                logger.info("Saved annotated frame to %s (saved=%d)", out_path, saved)

            if args.max_frames > 0 and frames >= args.max_frames:
                logger.info("Reached max_frames=%d, exiting.", args.max_frames)
                break

    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    finally:
        cap.release()

    return 0

if __name__ == "__main__":
    sys.exit(main())

