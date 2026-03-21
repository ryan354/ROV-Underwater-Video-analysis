#!/usr/bin/env python3
"""
ROV Watcher - Monitors folder for new videos and triggers analysis
"""
import os
import sys
import json
import time
import logging
import hashlib
import subprocess
import cv2
import numpy as np
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# === CONFIG FROM ENVIRONMENT ===
WATCH_FOLDER = os.getenv("WATCH_FOLDER", r"D:\ROV_Videos")
OUTPUT_FOLDER = os.getenv("OUTPUT_FOLDER", r"D:\ROV_Jobs")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
PYTHON_EXE = os.getenv("PYTHON_EXE", "python")
FRAME_EVERY_SEC = int(os.getenv("FRAME_EVERY_SEC", "5"))
MIN_FILE_SIZE_MB = float(os.getenv("MIN_FILE_SIZE_MB", "1"))
SUPPORTED_EXTS = [".mp4", ".avi", ".mkv", ".mov"]

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)


def send_telegram(message):
    if TELEGRAM_BOT_TOKEN:
        try:
            requests.post(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                json={"chat_id": TELEGRAM_CHAT_ID, "text": message},
                timeout=10
            )
        except:
            pass


def get_video_hash(video_path):
    with open(video_path, "rb") as f:
        return hashlib.md5(f.read(1024*1024)).hexdigest()


def extract_frames(video_path, output_dir, every_n_seconds=5):
    os.makedirs(output_dir, exist_ok=True)
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    interval = int(fps * every_n_seconds)
    frames = []
    
    frame_idx = 0
    saved = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if frame_idx % interval == 0:
            frame_path = os.path.join(output_dir, f"frame_{saved:04d}.jpg")
            cv2.imwrite(frame_path, frame)
            frames.append(frame_path)
            saved += 1
        frame_idx += 1
    
    cap.release()
    log.info(f"Extracted {saved} frames to {output_dir}")
    return frames


def process_video(video_path):
    video_path = Path(video_path)
    file_size_mb = video_path.stat().st_size / (1024*1024)
    if file_size_mb < MIN_FILE_SIZE_MB:
        log.info(f"Skipping small file: {video_path.name} ({file_size_mb:.1f}MB)")
        return
    
    log.info(f"Processing: {video_path.name} ({file_size_mb:.1f}MB)")
    
    # Create job folder
    job_name = f"{video_path.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    job_dir = Path(OUTPUT_FOLDER) / job_name
    frames_dir = job_dir / "frames"
    os.makedirs(frames_dir, exist_ok=True)
    
    # Extract frames
    extract_frames(str(video_path), str(frames_dir), FRAME_EVERY_SEC)
    
    # Save metadata
    meta = {
        "video": str(video_path),
        "size_mb": round(file_size_mb, 2),
        "processed_at": datetime.now().isoformat()
    }
    with open(job_dir / "job_meta.json", "w") as f:
        json.dump(meta, f, indent=2)
    
    send_telegram(f"📹 New video processed: {video_path.name}\nJob: {job_name}")
    log.info(f"Job created: {job_name}")


def scan_folder():
    watched = Path(WATCH_FOLDER)
    if not watched.exists():
        log.error(f"Watch folder not found: {WATCH_FOLDER}")
        return
    
    processed_hashes_file = watched / ".processed_hashes.txt"
    if processed_hashes_file.exists():
        with open(processed_hashes_file) as f:
            processed = set(f.read().strip().splitlines())
    else:
        processed = set()
    
    for ext in SUPPORTED_EXTS:
        for video in watched.glob(f"*{ext}"):
            if video.name.startswith("."):
                continue
            try:
                video_hash = get_video_hash(video)
                if video_hash not in processed:
                    process_video(video)
                    processed.add(video_hash)
                    with open(processed_hashes_file, "a") as f:
                        f.write(video_hash + "\n")
            except Exception as e:
                log.error(f"Error processing {video}: {e}")


if __name__ == "__main__":
    import requests
    log.info(f"Watching: {WATCH_FOLDER}")
    log.info("Press Ctrl+C to stop...")
    
    while True:
        scan_folder()
        time.sleep(10)
