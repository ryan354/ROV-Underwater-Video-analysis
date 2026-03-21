#!/usr/bin/env python3
"""
ROV AI Analyzer - Simplified Version
Reads job_meta.json, runs AI vision analysis, generates PDF report.
"""
import os
import sys
import json
import base64
import time
import logging
import requests
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from fpdf import FPDF

load_dotenv()

# === CONFIG FROM ENVIRONMENT ===
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
OUTPUT_FOLDER = os.getenv("OUTPUT_FOLDER", r"D:\ROV_Jobs")
REPORTS_FOLDER = os.getenv("REPORTS_FOLDER", r"D:\ROV_Reports")
MODEL_ID = os.getenv("MODEL_ID", "google/gemini-2.5-flash-lite")
OR_API_URL = os.getenv("OR_API_URL", "https://openrouter.ai/api/v1/chat/completions")
VERIFICATION_MODE = os.getenv("VERIFICATION_MODE", "false").lower() == "true"
VERIFICATION_MAX_FRAMES = int(os.getenv("VERIFICATION_MAX_FRAMES", "5"))
APPROVAL_TIMEOUT_SEC = int(os.getenv("APPROVAL_TIMEOUT_SEC", "600"))

# === LOGGING ===
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
log = logging.getLogger(__name__)


def send_telegram(message):
    if not TELEGRAM_BOT_TOKEN:
        log.warning("Telegram bot token not set")
        return
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"},
            timeout=10
        )
    except Exception as e:
        log.warning(f"Telegram failed: {e}")


def send_telegram_file(file_path, caption=""):
    if not TELEGRAM_BOT_TOKEN or not os.path.exists(file_path):
        return
    try:
        with open(file_path, "rb") as f:
            requests.post(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument",
                files={"document": (os.path.basename(file_path), f)},
                data={"chat_id": TELEGRAM_CHAT_ID, "caption": caption},
                timeout=30
            )
    except Exception as e:
        log.warning(f"Telegram file send failed: {e}")


def encode_image(image_path):
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def analyze_frame(image_path, prompt):
    if not OPENROUTER_API_KEY:
        return "[OPENROUTER_API_KEY not set]"
    
    try:
        image_b64 = encode_image(image_path)
        response = requests.post(
            OR_API_URL,
            headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}", "Content-Type": "application/json"},
            json={
                "model": MODEL_ID,
                "messages": [{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}}
                    ]
                }]
            },
            timeout=60
        )
        result = response.json()
        return result.get("choices", [{}])[0].get("message", {}).get("content", "[No response]")
    except Exception as e:
        return f"[Error: {e}]"


class ReportPDF(FPDF):
    def header(self):
        self.set_font("Arial", "B", 15)
        self.cell(0, 10, "ROV Inspection Report", 0, 1, "C")
        self.ln(5)


def generate_pdf(job_name, frames_data, output_path):
    pdf = ReportPDF()
    pdf.add_page()
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 10, f"Job: {job_name}", 0, 1)
    pdf.cell(0, 10, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", 0, 1)
    pdf.ln(5)
    
    for i, (frame, analysis) in enumerate(frames_data):
        pdf.set_font("Arial", "B", 11)
        pdf.cell(0, 8, f"Frame {i+1}: {os.path.basename(frame)}", 0, 1)
        pdf.set_font("Arial", "", 9)
        pdf.multi_cell(0, 5, analysis[:500])
        pdf.ln(3)
    
    pdf.output(output_path)
    return output_path


def get_latest_job():
    jobs = [d for d in Path(OUTPUT_FOLDER).iterdir() if d.is_dir()]
    if not jobs:
        return None
    return max(jobs, key=lambda x: x.stat().st_mtime)


def analyze_job(job_path):
    job_path = Path(job_path)
    meta_file = job_path / "job_meta.json"
    
    if not meta_file.exists():
        log.error(f"No job_meta.json in {job_path}")
        return
    
    with open(meta_file) as f:
        meta = json.load(f)
    
    frames_dir = job_path / "frames"
    if not frames_dir.exists():
        log.error("No frames folder")
        return
    
    frames = sorted(frames_dir.glob("*.jpg"))[:VERIFICATION_MAX_FRAMES if VERIFICATION_MODE else 100]
    log.info(f"Analyzing {len(frames)} frames...")
    
    prompt = """Analyze this ROV underwater inspection frame. Describe:
1. Overall condition (good/acceptable/poor)
2. Any visible defects, corrosion, damage
3. Anomalies or areas of concern
4. Recommendations"""

    results = []
    for i, frame in enumerate(frames):
        log.info(f"Processing frame {i+1}/{len(frames)}: {frame.name}")
        analysis = analyze_frame(str(frame), prompt)
        results.append((str(frame), analysis))
        time.sleep(1)
    
    # Generate PDF
    os.makedirs(REPORTS_FOLDER, exist_ok=True)
    pdf_path = Path(REPORTS_FOLDER) / f"{job_path.name}_report.pdf"
    generate_pdf(job_path.name, results, str(pdf_path))
    log.info(f"Report saved: {pdf_path}")
    
    send_telegram(f"✅ Analysis complete for {job_path.name}")
    send_telegram_file(str(pdf_path), "📊 Inspection Report")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        job = sys.argv[1]
    else:
        job = get_latest_job()
    
    if job:
        log.info(f"Analyzing job: {job}")
        analyze_job(job)
    else:
        log.error("No job found. Specify path or ensure jobs exist in OUTPUT_FOLDER")
