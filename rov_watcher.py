#!/usr/bin/env python3

import os
import re
import cv2
import sys
import time
import json
import shutil
import hashlib
import logging
import subprocess
import numpy as np
from pathlib import Path
from datetime import datetime

import requests

# ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?
# SETTINGS ƒ?" edit these
# ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?

WATCH_FOLDER    = r"D:\ROV_Videos"
OUTPUT_FOLDER   = r"D:\ROV_Jobs"

TELEGRAM_BOT_TOKEN = "xxxx"
TELEGRAM_CHAT_ID   = "xxxx"

# Path to Python + analyzer script (must be in same folder as watcher)
PYTHON_EXE      = r"C:\Users\ryaan\anaconda3\envs\FormulatrixTest\python.exe"
ANALYZER_SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "rov_analyzer.py")

# ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?
# OPTIONAL ƒ?" tune these
# ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?

FRAME_EVERY_SEC       = 5
MIN_FILE_SIZE_MB      = 1
SUPPORTED_EXTS        = [".mp4", ".avi", ".mkv", ".mov"]

MOTION_THRESHOLD      = 25
MOTION_MIN_AREA       = 800
MOTION_MIN_CONTOURS   = 2
FEATURE_MIN_KEYPOINTS = 80
EDGE_DENSITY_MIN      = 0.04
DARK_SKIP_THRESHOLD   = 20
TURBID_FLAG_THRESHOLD = 180
COLOUR_ANOMALY_RATIO  = 0.02

APPROVAL_TIMEOUT_SEC  = 600    # 10 minutes to reply

# ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("rov_watcher.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)
processed_hashes = set()


# ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?
# TELEGRAM
# ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?

def send_telegram(message):
    if not TELEGRAM_BOT_TOKEN:
        return
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID,
                  "text": message, "parse_mode": "Markdown"},
            timeout=10
        )
        log.info("Telegram sent.")
    except Exception as e:
        log.warning(f"Telegram failed: {e}")


def get_latest_update_id():
    """Get the current latest update_id so we only read NEW messages."""
    try:
        r = requests.get(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates",
            params={"limit": 1, "offset": -1}, timeout=10
        )
        results = r.json().get("result", [])
        if results:
            return results[-1]["update_id"]
    except Exception:
        pass
    return 0


def wait_for_approval(prompt_msg, timeout_sec=600):
    """
    Send prompt_msg, then long-poll Telegram until user replies YES or NO.
    Returns True = approved, False = denied or timed out.
    """
    send_telegram(prompt_msg)
    offset   = get_latest_update_id() + 1
    deadline = time.time() + timeout_sec
    log.info(f"Waiting for Telegram reply (timeout {timeout_sec}s)...")

    YES_WORDS = {"yes","y","approve","approved","ok","go","proceed","run","start","ya","yep"}
    NO_WORDS  = {"no","n","cancel","skip","stop","deny","nope","nah"}

    while time.time() < deadline:
        try:
            r = requests.get(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates",
                params={"offset": offset, "timeout": 20},
                timeout=30
            )
            for upd in r.json().get("result", []):
                offset = upd["update_id"] + 1
                msg    = upd.get("message", {})
                if str(msg.get("chat",{}).get("id","")) != str(TELEGRAM_CHAT_ID):
                    continue
                text = msg.get("text","").strip().lower()
                if text in YES_WORDS:
                    log.info("Reply: YES")
                    send_telegram("ƒo. *Approved!* Starting now...")
                    return True
                if text in NO_WORDS:
                    log.info("Reply: NO")
                    send_telegram("ƒ?,‹,? *Cancelled.* I will not proceed.")
                    return False
        except Exception as e:
            log.warning(f"Poll error: {e}")
            time.sleep(5)

    log.warning("Approval timeout.")
    send_telegram(
        f"ƒ?ø *No reply after {timeout_sec//60} min ƒ?" cancelled.*\n"
        f"Drop the video again or run the analyzer manually."
    )
    return False


# ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?
# TELEMETRY
# ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?

def find_subtitle_file(video_path):
    base   = Path(video_path).stem
    folder = Path(video_path).parent
    for ext in [".srt", ".txt", ".csv", ".vtt", ".ass",".csv"]:
        c = folder / (base + ext)
        if c.exists():
            log.info(f"Telemetry: {c.name}")
            return str(c)
    log.info("No telemetry file found.")
    return None


def parse_telemetry_srt(srt_path):
    telemetry = []
    if not srt_path or not os.path.exists(srt_path):
        return telemetry
    with open(srt_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    for block in re.split(r"\n\n+", content.strip()):
        lines     = block.strip().split("\n")
        if len(lines) < 3:
            continue
        ts        = re.match(r"(\d+:\d+:\d+),\d+", lines[1]) if len(lines)>1 else None
        timestamp = ts.group(1) if ts else "00:00:00"
        text      = " ".join(lines[2:])
        entry     = {"timestamp": timestamp, "raw": text}
        for key, pat in [
            ("altitude", r"[Aa]lt(?:itude)?[:\s]+([+-]?\d+\.?\d*)"),
            ("depth",    r"[Dd]epth[:\s]+([+-]?\d+\.?\d*)"),
            ("pitch",    r"[Pp]itch[:\s]+([+-]?\d+\.?\d*)"),
            ("roll",     r"[Rr]oll[:\s]+([+-]?\d+\.?\d*)"),
            ("speed",    r"[Ss]peed[:\s]+([+-]?\d+\.?\d*)"),
            ("heading",  r"[Hh]ead(?:ing)?[:\s]+([+-]?\d+\.?\d*)"),
            ("temp",     r"[Tt]emp(?:erature)?[:\s]+([+-]?\d+\.?\d*)"),
        ]:
            m = re.search(pat, text)
            if m:
                entry[key] = float(m.group(1))
        telemetry.append(entry)
    log.info(f"Parsed {len(telemetry)} telemetry entries.")
    return telemetry



def parse_telemetry_csv(csv_path):
    """Parse CSV telemetry file."""
    import csv
    telemetry = []
    if not csv_path or not os.path.exists(csv_path):
        return telemetry
    try:
        with open(csv_path, "r", encoding="utf-8", errors="ignore") as f:
            reader = csv.DictReader(f)
            for row in reader:
                entry = {"timestamp": row.get("timestamp", "00:00:00")}
                for key, col in [
                    ("altitude", ["altitude", "alt", "alt_m"]),
                    ("depth", ["depth", "depth_m"]),
                    ("pitch", ["pitch", "pitch_deg"]),
                    ("roll", ["roll", "roll_deg"]),
                    ("speed", ["speed", "speed_kn"]),
                    ("heading", ["heading", "hdg", "heading_deg"]),
                    ("temp", ["temp", "temperature", "temp_c"]),
                ]:
                    for cn in col:
                        if cn in row:
                            try:
                                entry[key] = float(row[cn])
                                break
                            except: pass
                if len(entry) == 1:
                    entry["raw"] = str(row)
                telemetry.append(entry)
        log.info(f"Parsed {len(telemetry)} CSV entries.")
    except Exception as e:
        log.warning(f"CSV error: {e}")
    return telemetry


def parse_telemetry_ass(ass_path):
    """Parse ASS/SSA telemetry file."""
    telemetry = []
    if not ass_path or not os.path.exists(ass_path):
        return telemetry
    try:
        with open(ass_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        events = re.search(r"(?s)\[Events\](.*?)(?:\n\[|\Z)", content)
        if not events: return telemetry
        for line in events.group(1).strip().split("`n"):
            if not line.startswith("Dialogue:"): continue
            parts = line[9:].split(",", 9)
            if len(parts) < 10: continue
            ts = parts[1].strip()[:8]
            txt = parts[9].strip()
            entry = {"timestamp": ts, "raw": txt}
            for key, pat in [
                ("altitude", r"[Aa]lt[:\s]+([+-]?\d+\.?\d*)"),
                ("depth", r"[Dd]epth[:\s]+([+-]?\d+\.?\d*)"),
                ("pitch", r"[Pp]itch[:\s]+([+-]?\d+\.?\d*)"),
                ("roll", r"[Rr]oll[:\s]+([+-]?\d+\.?\d*)"),
                ("speed", r"[Ss]peed[:\s]+([+-]?\d+\.?\d*)"),
                ("heading", r"[Hh]ead[:\s]+([+-]?\d+\.?\d*)"),
                ("temp", r"[Tt]emp[:\s]+([+-]?\d+\.?\d*)"),
            ]:
                m = re.search(pat, txt)
                if m: entry[key] = float(m.group(1))
            telemetry.append(entry)
        log.info(f"Parsed {len(telemetry)} ASS entries.")
    except Exception as e:
        log.warning(f"ASS error: {e}")
    return telemetry


def load_telemetry(video_path):
    """Load telemetry from any supported file."""
    sub_path = find_subtitle_file(video_path)
    if not sub_path: return []
    ext = os.path.splitext(sub_path)[1].lower()
    if ext == ".csv": return parse_telemetry_csv(sub_path)
    if ext in [".ass", ".ssa"]: return parse_telemetry_ass(sub_path)
    return parse_telemetry_srt(sub_path)


def get_telemetry_at(frame_index, telemetry, every_n_sec):
    frame_sec = frame_index * every_n_sec
    h,m,s     = frame_sec//3600, (frame_sec%3600)//60, frame_sec%60
    best      = {"timestamp": f"{h:02d}:{m:02d}:{s:02d}"}
    best_diff = float("inf")
    for entry in telemetry:
        try:
            p    = entry["timestamp"].split(":")
            esec = int(p[0])*3600+int(p[1])*60+int(p[2])
            diff = abs(esec - frame_sec)
            if diff < best_diff:
                best_diff = diff
                best = entry
        except Exception:
            continue
    return best


# ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?
# FRAME EXTRACTION
# ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?

def extract_frames(video_path, out_dir, every_n_sec=3):
    os.makedirs(out_dir, exist_ok=True)
    pattern = os.path.join(out_dir, "frame_%05d.jpg")
    cmd = ["ffmpeg","-i",video_path,"-vf",f"fps=1/{every_n_sec}",
           "-q:v","2","-y",pattern]
    log.info(f"Extracting 1 frame every {every_n_sec}s...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        log.error(f"ffmpeg error:\n{result.stderr[-400:]}")
        return []
    frames = sorted(Path(out_dir).glob("frame_*.jpg"))
    log.info(f"Extracted {len(frames)} frames.")
    return [str(f) for f in frames]


# ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?
# OPENCV STAGE 1
# ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?

class OpenCVAnalyzer:
    def __init__(self):
        self.prev_gray = None
        self.orb       = cv2.ORB_create(nfeatures=500)

    def analyze(self, frame_path):
        img = cv2.imread(frame_path)
        if img is None:
            self.prev_gray = None
            return {"error": "unreadable"}
        gray       = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        brightness = float(np.mean(gray))
        if brightness < DARK_SKIP_THRESHOLD:
            return {"skip": f"too dark ({brightness:.1f})"}
        flags = {}

        if self.prev_gray is not None:
            diff      = cv2.absdiff(self.prev_gray, gray)
            _, thresh = cv2.threshold(diff, MOTION_THRESHOLD, 255, cv2.THRESH_BINARY)
            k         = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(5,5))
            thresh    = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, k)
            thresh    = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, k)
            contours,_ = cv2.findContours(thresh,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
            big = [c for c in contours if cv2.contourArea(c) > MOTION_MIN_AREA]
            if len(big) >= MOTION_MIN_CONTOURS:
                flags["motion"] = {
                    "contour_count": len(big),
                    "total_area_px": int(sum(cv2.contourArea(c) for c in big)),
                    "reason": "Moving object or ROV movement detected"
                }

        kps,_ = self.orb.detectAndCompute(gray, None)
        if len(kps) >= FEATURE_MIN_KEYPOINTS:
            flags["features"] = {"keypoint_count": len(kps),
                                  "reason": "Rich texture or structure detected"}

        edges = cv2.Canny(gray, 50, 150)
        edge_density = float(np.count_nonzero(edges))/(gray.shape[0]*gray.shape[1])
        if edge_density >= EDGE_DENSITY_MIN:
            flags["edges"] = {"density": round(edge_density,4),
                               "reason": "High edge density ƒ?" possible structure"}

        if brightness > TURBID_FLAG_THRESHOLD:
            flags["turbidity"] = {"brightness": round(brightness,1),
                                   "reason": "High brightness ƒ?" turbidity or light"}

        hsv   = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        red1  = cv2.inRange(hsv,(0,  50,50),(10, 255,255))
        red2  = cv2.inRange(hsv,(160,50,50),(180,255,255))
        orange= cv2.inRange(hsv,(10, 50,50),(30, 255,255))
        ratio = (cv2.countNonZero(red1)+cv2.countNonZero(red2)+
                 cv2.countNonZero(orange))/(img.shape[0]*img.shape[1])
        if ratio > COLOUR_ANOMALY_RATIO:
            flags["colour"] = {"unusual_ratio": round(ratio,4),
                                "reason": "Unusual colour ƒ?" marine life, rust, or debris"}

        self.prev_gray = gray
        return flags


def draw_annotations(frame_path, flags, out_path):
    img = cv2.imread(frame_path)
    if img is None:
        shutil.copy(frame_path, out_path)
        return
    cv2.rectangle(img,(0,0),(img.shape[1]-1,img.shape[0]-1),(0,0,220),5)
    y = 32
    for name, info in flags.items():
        cv2.putText(img, f"{name.upper()}: {info.get('reason','')}", (10,y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,255), 2, cv2.LINE_AA)
        y += 30
    cv2.imwrite(out_path, img)


# ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?
# MAIN PIPELINE
# ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?

def process_video(video_path):
    log.info(f"\n{'='*55}")
    log.info(f"NEW VIDEO: {os.path.basename(video_path)}")
    log.info(f"{'='*55}")

    size_mb = os.path.getsize(video_path)/(1024*1024)
    if size_mb < MIN_FILE_SIZE_MB:
        log.warning(f"Too small ({size_mb:.1f}MB) ƒ?" skipping.")
        return

    h = hashlib.md5(open(video_path,"rb").read(65536)).hexdigest()
    if h in processed_hashes:
        log.info("Already processed ƒ?" skipping.")
        return
    processed_hashes.add(h)

    video_name  = Path(video_path).stem
    ts          = datetime.now().strftime("%Y%m%d_%H%M%S")
    job_id      = f"{video_name}_{ts}"
    job_dir     = os.path.join(OUTPUT_FOLDER, job_id)
    frames_dir  = os.path.join(job_dir, "all_frames")
    flagged_dir = os.path.join(job_dir, "flagged_frames")
    os.makedirs(frames_dir,  exist_ok=True)
    os.makedirs(flagged_dir, exist_ok=True)
    log.info(f"Job ID: {job_id}")

    sub_path  = find_subtitle_file(video_path)
    telemetry = load_telemetry(video_path)
    frames    = extract_frames(video_path, frames_dir, FRAME_EVERY_SEC)

    if not frames:
        send_telegram(
            f"ƒ?O *ROV Watcher Error*\n"
            f"No frames extracted from `{os.path.basename(video_path)}`\n"
            f"Check ffmpeg installation."
        )
        return

    log.info(f"\n-- OpenCV Stage 1 ({len(frames)} frames) --")
    analyzer       = OpenCVAnalyzer()
    stage1_results = []
    flagged_list   = []
    skipped_count  = 0

    for i, frame_path in enumerate(frames):
        fname   = os.path.basename(frame_path)
        telem   = get_telemetry_at(i, telemetry, FRAME_EVERY_SEC)
        flags   = analyzer.analyze(frame_path)
        skipped = "skip" in flags or "error" in flags
        flagged = not skipped and len(flags) > 0

        result = {
            "frame": fname, "frame_idx": i,
            "timestamp": telem.get("timestamp","00:00:00"),
            "telemetry": telem, "cv_flags": flags,
            "flagged": flagged, "skipped": skipped,
        }
        stage1_results.append(result)

        if skipped:
            skipped_count += 1
            log.info(f"  [{i+1:4d}/{len(frames)}] SKIP  {fname}")
        elif flagged:
            flagged_list.append(result)
            log.info(f"  [{i+1:4d}/{len(frames)}] FLAG  {fname} -> {' | '.join(flags.keys())}")
            draw_annotations(frame_path, flags, os.path.join(flagged_dir, fname))
        else:
            log.info(f"  [{i+1:4d}/{len(frames)}] CLEAR {fname}")

    total_frames  = len(frames)
    flagged_count = len(flagged_list)
    clear_count   = total_frames - flagged_count - skipped_count
    savings_pct   = int(100*(total_frames-flagged_count)/max(total_frames,1))

    log.info(f"  Total: {total_frames} | Flagged: {flagged_count} | "
             f"Clear: {clear_count} | Skipped: {skipped_count}")

    # Save job metadata
    meta = {
        "job_id": job_id,
        "video_file": os.path.basename(video_path),
        "video_path": video_path,
        "subtitle_path": sub_path,
        "created_at": datetime.now().isoformat(),
        "total_frames": total_frames,
        "flagged_count": flagged_count,
        "clear_count": clear_count,
        "skipped_count": skipped_count,
        "frame_interval_sec": FRAME_EVERY_SEC,
        "job_dir": job_dir,
        "flagged_dir": flagged_dir,
        "stage1_results": stage1_results,
        "flagged_list": flagged_list,
        "status": "ready_for_analysis",
    }
    meta_path = os.path.join(job_dir, "job_meta.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)
    log.info(f"Job saved: {meta_path}")

    # ƒ"?ƒ"? All clear ƒ?" just notify, no approval needed ƒ"?ƒ"?ƒ"?
    if flagged_count == 0:
        send_telegram(
            f"dY¨ *ROV Watcher ƒ?" Extraction Complete*\n"
            f"dY"1 `{os.path.basename(video_path)}`\n\n"
            f"dY-¬‹,? Frames: *{total_frames}*\n"
            f"ƒo. All clear ƒ?" no interesting frames flagged.\n"
            f"No AI analysis needed."
        )
        return

    # ƒ"?ƒ"? Ask approval to run analyzer ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?
    flag_types = set()
    for item in flagged_list:
        flag_types.update(item["cv_flags"].keys())

    approved = wait_for_approval(
        f"dY¨ *ROV Watcher ƒ?" Extraction Complete*\n"
        f"dY"1 `{os.path.basename(video_path)}`\n\n"
        f"dY-¬‹,? Total frames:   *{total_frames}*\n"
        f"dY"' Flagged frames: *{flagged_count}* ({100-savings_pct}%)\n"
        f"ƒo. Clear frames:   *{clear_count}*\n"
        f"dY'ø API savings:    *~{savings_pct}%*\n\n"
        f"dY"? CV signals: {', '.join(sorted(flag_types))}\n"
        f"dY"? Job: `{job_id}`\n\n"
        f"ƒ?3 *Reply YES to start Gemini analysis*\n"
        f"Reply NO to skip.\n"
        f"_(Timeout: {APPROVAL_TIMEOUT_SEC//60} min)_",
        APPROVAL_TIMEOUT_SEC
    )

    if approved:
        log.info("Launching analyzer...")
        subprocess.Popen(
            [PYTHON_EXE, ANALYZER_SCRIPT, job_dir],
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
    else:
        log.info("Analyzer skipped.")


# ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?
# MAIN ƒ?" run once and exit
# ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?

def find_latest_video():
    """Find the most recently modified video in WATCH_FOLDER."""
    videos = []
    for ext in SUPPORTED_EXTS:
        videos.extend(Path(WATCH_FOLDER).glob(f"*{ext}"))
    if not videos:
        return None
    return str(max(videos, key=lambda p: p.stat().st_mtime))


def main():
    log.info("ROV Watcher v5 ƒ?" Run Once Mode")
    log.info(f"Watch:    {WATCH_FOLDER}")
    log.info(f"Output:   {OUTPUT_FOLDER}")

    os.makedirs(WATCH_FOLDER,  exist_ok=True)
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    # Accept video path directly as argument, or auto-find latest
    if len(sys.argv) >= 2:
        video_path = sys.argv[1]
        if not os.path.exists(video_path):
            log.error(f"File not found: {video_path}")
            sys.exit(1)
        log.info(f"Using specified video: {video_path}")
    else:
        log.info("No video specified ƒ?" finding latest in watch folder...")
        video_path = find_latest_video()
        if not video_path:
            log.error(f"No video files found in {WATCH_FOLDER}")
            log.error(f"Supported formats: {SUPPORTED_EXTS}")
            sys.exit(1)
        log.info(f"Found: {video_path}")

    # Process the video and exit
    process_video(video_path)
    log.info("\nDone. Exiting.")


if __name__ == "__main__":
    main()
