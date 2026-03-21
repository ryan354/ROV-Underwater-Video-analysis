#!/usr/bin/env python3
# ROV ANALYZER v4
# Reads job_meta.json, runs Gemini vision analysis,
# asks Telegram approval, generates PDF report.
#
# INSTALL: pip install requests fpdf2
#
# RUN: python rov_analyzer.py              (auto-detect latest job)
#      python rov_analyzer.py C:/ROV_Jobs/myjob  (specific job)

import os
import sys
import json
import base64
import time
import logging
import requests
from pathlib import Path
from datetime import datetime
from fpdf import FPDF

# ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?
# SETTINGS ƒ?" edit these
# ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?

OPENROUTER_API_KEY  = "xxxx"
TELEGRAM_BOT_TOKEN  = "xxxx"
TELEGRAM_CHAT_ID    = "xxxx"

OUTPUT_FOLDER       = r"D:\ROV_Jobs"
REPORTS_FOLDER      = r"D:\ROV_Reports"

# ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?
MODEL_ID   = "google/gemini-2.5-flash-lite"
OR_API_URL = "https://openrouter.ai/api/v1/chat/completions"

VERIFICATION_MODE       = False   # True = sample 5 frames only (for testing)
VERIFICATION_MAX_FRAMES = 20

APPROVAL_TIMEOUT_SEC    = 600     # 10 minutes to reply
# ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("rov_analyzer.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)


# ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?
# TELEGRAM ƒ?" send text / send file / poll approval
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
                timeout=120
            )
        log.info(f"File sent: {os.path.basename(file_path)}")
    except Exception as e:
        log.warning(f"File send failed: {e}")


def get_latest_update_id():
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
    Send prompt_msg, poll Telegram for YES/NO.
    Returns True = approved, False = denied/timeout.
    """
    send_telegram(prompt_msg)
    offset   = get_latest_update_id() + 1
    deadline = time.time() + timeout_sec
    log.info(f"Waiting for reply (timeout {timeout_sec}s)...")

    YES = {"yes","y","approve","approved","ok","go","proceed","ya","yep","sure"}
    NO  = {"no","n","cancel","skip","stop","deny","nope","nah"}

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
                if text in YES:
                    log.info("Reply: YES")
                    send_telegram("ƒo. *Approved!* Working on it...")
                    return True
                if text in NO:
                    log.info("Reply: NO")
                    send_telegram("ƒ?,‹,? *Skipped.* PDF will not be generated.")
                    return False
        except Exception as e:
            log.warning(f"Poll error: {e}")
            time.sleep(5)

    log.warning("Timeout ƒ?" no reply.")
    send_telegram(
        f"ƒ?ø *No reply after {timeout_sec//60} min.*\n"
        f"PDF not generated. Run the analyzer again to retry."
    )
    return False


# ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?
# GEMINI VISION VIA OPENROUTER
# ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?

ANALYSIS_PROMPT = """\
You are an expert underwater ROV video analyst with knowledge in marine biology,
subsea engineering, underwater archaeology, and oceanography.

This frame was pre-selected by OpenCV motion/feature detection.

ROV Telemetry: {telemetry}
OpenCV signals: {cv_flags}

Analyze this underwater image and respond ONLY with valid JSON:
{{
  "objects": {{
    "detected": true,
    "list": ["fish", "crab"],
    "details": "description with size estimates and behavior"
  }},
  "structures": {{
    "detected": false,
    "list": [],
    "details": null
  }},
  "anomalies": {{
    "detected": false,
    "description": null
  }},
  "seabed": {{
    "visible": true,
    "type": "sandy with scattered rocks",
    "depth_estimate": "5-10m based on light"
  }},
  "visibility": "good",
  "water_clarity": "clear",
  "urgency": "low",
  "urgency_reason": "marine life only, no structural concerns",
  "confidence": 0.82,
  "one_line_summary": "Two reef fish near sandy seabed"
}}
Urgency: none/low/medium/high. Respond ONLY with JSON, no markdown fences.
"""


def fmt_telemetry(t):
    units = {"depth":"m","altitude":"m","pitch":"deg",
             "roll":"deg","speed":"kn","heading":"deg","temp":"C"}
    parts = [f"{k.capitalize()}: {t[k]}{u}" for k,u in units.items() if k in t]
    return "  |  ".join(parts) or f"Timestamp: {t.get('timestamp','N/A')}"


def fmt_flags(flags):
    return "  |  ".join(
        f"{n.upper()}: {i.get('reason','')}" for n,i in flags.items()
    ) if flags else "General interest"


def analyze_frame(image_path, telemetry, cv_flags):
    with open(image_path, "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode("utf-8")

    payload = {
        "model": MODEL_ID,
        "max_tokens": 700,
        "messages": [{
            "role": "user",
            "content": [
                {"type": "image_url",
                 "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}},
                {"type": "text",
                 "text": ANALYSIS_PROMPT.format(
                     telemetry=fmt_telemetry(telemetry),
                     cv_flags=fmt_flags(cv_flags)
                 )}
            ]
        }]
    }
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type":  "application/json",
        "HTTP-Referer":  "https://rov-analyzer.local",
        "X-Title":       "ROV Underwater Analyzer"
    }
    try:
        r = requests.post(OR_API_URL, headers=headers,
                          json=payload, timeout=45)
        r.raise_for_status()
        raw = r.json()["choices"][0]["message"]["content"].strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw.strip())
    except Exception as e:
        log.error(f"API error: {e}")
        return {
            "objects":    {"detected": False, "list": [], "details": None},
            "structures": {"detected": False, "list": [], "details": None},
            "anomalies":  {"detected": False, "description": None},
            "seabed":     {"visible": False, "type": "unknown"},
            "visibility": "unknown", "water_clarity": "unknown",
            "urgency": "none", "urgency_reason": "API error",
            "confidence": 0.0,
            "one_line_summary": f"API error: {str(e)[:80]}"
        }


# ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?
# PDF GENERATION  (fpdf2 ƒ?" ASCII text only, no emoji)
# ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?

URGENCY_RGB = {
    "high":   (180, 0,   0),
    "medium": (190, 95,  0),
    "low":    (0,   110, 50),
    "none":   (70,  70,  70),
}


def safe(text):
    """Strip characters outside Latin-1 to avoid fpdf2 encoding errors."""
    if not text:
        return ""
    return str(text).encode("latin-1", errors="replace").decode("latin-1")


def generate_pdf(job_meta, findings, output_path):
    """
    Generate a professional PDF report using fpdf2.
    All text is ASCII/Latin-1 safe ƒ?" no emoji inside PDF cells.
    Uses new_x/new_y API (fpdf2 >= 2.5.2) ƒ?" no ln= deprecation warnings.
    """
    from fpdf.enums import XPos, YPos

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    PAGE_H        = 297
    BOTTOM_MARGIN = 15
    CARD_MIN_H    = 75

    # ƒ"?ƒ"? Header banner ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?
    pdf.set_fill_color(15, 40, 75)
    pdf.rect(0, 0, 210, 42, "F")
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_xy(10, 7)
    pdf.cell(0, 10, "ROV UNDERWATER ANALYSIS REPORT",
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_x(10)
    pdf.cell(0, 6,
             f"Video: {safe(job_meta['video_file'])}  |  "
             f"Model: {MODEL_ID}  |  "
             f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    # Verification banner
    if VERIFICATION_MODE:
        pdf.set_fill_color(200, 100, 0)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Helvetica", "B", 10)
        total_f = job_meta.get("flagged_count", len(findings))
        pdf.cell(0, 9,
                 f"  [SYSTEM VERIFICATION]  {len(findings)} of {total_f} "
                 f"flagged frames sampled  --  NOT a full analysis",
                 fill=True,
                 new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.set_text_color(0, 0, 0)
    pdf.set_y(50)

    # ƒ"?ƒ"? Summary table ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?
    total_a = len(findings)
    high_u  = sum(1 for f in findings if f.get("analysis",{}).get("urgency")=="high")
    med_u   = sum(1 for f in findings if f.get("analysis",{}).get("urgency")=="medium")
    all_obj = sorted({str(o) for f in findings
                      for o in f.get("analysis",{}).get("objects",{}).get("list",[])
                      if not isinstance(o, dict)})
    all_str = sorted({str(s) for f in findings
                      for s in f.get("analysis",{}).get("structures",{}).get("list",[])
                      if not isinstance(s, dict)})
    savings = job_meta["total_frames"] - len(findings)

    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 7, "SUMMARY", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    LABEL_W = 60
    VALUE_W = 130

    def truncate(text, max_chars=90):
        s = safe(str(text))
        return s if len(s) <= max_chars else s[:max_chars].rstrip(", ") + "..."

    def irow(label, val, alt=False):
        pdf.set_fill_color(238, 244, 255) if alt else pdf.set_fill_color(255, 255, 255)
        row_y = pdf.get_y()
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_xy(pdf.l_margin, row_y)
        pdf.cell(LABEL_W, 6, f"  {safe(label)}", border=1, fill=True)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_xy(pdf.l_margin + LABEL_W, row_y)
        pdf.cell(VALUE_W, 6, f"  {truncate(val)}", border=1, fill=False,
                 new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    irow("Job ID",          job_meta["job_id"],         True)
    irow("Video File",      job_meta["video_file"],      False)
    irow("Total Frames",    job_meta["total_frames"],    True)
    irow("OpenCV Flagged",  job_meta["flagged_count"],   False)
    irow("Gemini Analyzed", total_a,                     True)
    irow("API Calls Saved", savings,                     False)
    irow("High Urgency",    high_u,                      True)
    irow("Medium Urgency",  med_u,                       False)
    if all_obj:
        irow("Objects Found",    ", ".join(all_obj),     True)
    if all_str:
        irow("Structures Found", ", ".join(all_str),     False)

    # Full list below table if truncated
    if all_obj and len(", ".join(all_obj)) > 90:
        pdf.set_font("Helvetica", "I", 8)
        pdf.set_text_color(100, 100, 100)
        pdf.set_x(pdf.l_margin)
        pdf.multi_cell(190, 5, f"  Full objects: {safe(', '.join(all_obj))}")
        pdf.set_text_color(0, 0, 0)
    if all_str and len(", ".join(all_str)) > 90:
        pdf.set_font("Helvetica", "I", 8)
        pdf.set_text_color(100, 100, 100)
        pdf.set_x(pdf.l_margin)
        pdf.multi_cell(190, 5, f"  Full structures: {safe(', '.join(all_str))}")
        pdf.set_text_color(0, 0, 0)

    pdf.ln(5)

    # ƒ"?ƒ"? Detailed findings ƒ?" one card per frame ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 7, "DETAILED FINDINGS", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    for idx, item in enumerate(findings):
        a       = item.get("analysis") or {}
        telem   = item.get("telemetry", {})
        flags   = item.get("cv_flags", {})
        urgency = a.get("urgency", "none")
        r,g,b   = URGENCY_RGB.get(urgency, (70,70,70))

        # Safely unpack seabed ƒ?" Gemini sometimes returns null
        sb       = a.get("seabed") or {}
        sb_type  = safe(sb.get("type", "N/A") if sb else "N/A")
        sb_depth = safe(sb.get("depth_estimate", "N/A") if sb else "N/A")

        # Force new page if not enough room
        if PAGE_H - BOTTOM_MARGIN - pdf.get_y() < CARD_MIN_H:
            pdf.add_page()

        # Header bar ƒ?" multi_cell wraps if long
        pdf.set_fill_color(r, g, b)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_x(pdf.l_margin)
        pdf.multi_cell(190, 7,
                 f"  [{idx+1}] {safe(item['frame'])}  |  "
                 f"Time: {safe(telem.get('timestamp','N/A'))}  |  "
                 f"Urgency: {urgency.upper()}  |  "
                 f"Confidence: {a.get('confidence',0):.0%}",
                 fill=True)
        pdf.set_text_color(0, 0, 0)

        # Telemetry row ƒ?" auto-wraps if long
        pdf.set_fill_color(225, 238, 255)
        pdf.set_font("Helvetica", "", 8)
        pdf.set_x(pdf.l_margin)
        pdf.multi_cell(190, 5, f"  Telemetry: {safe(fmt_telemetry(telem))}",
                       fill=True)

        # CV signals row ƒ?" auto-wraps if long
        pdf.set_fill_color(242, 242, 242)
        pdf.set_x(pdf.l_margin)
        pdf.multi_cell(190, 5, f"  CV signals: {safe(fmt_flags(flags))}",
                       fill=True)

        # Disable auto page break while drawing card body
        pdf.set_auto_page_break(False)

        frame_img = item.get("frame_path")
        has_img   = frame_img and os.path.exists(frame_img)
        cur_y     = pdf.get_y() + 2
        text_x    = 72 if has_img else 10
        text_w    = 128 if has_img else 190

        if has_img:
            try:
                pdf.image(frame_img, x=10, y=cur_y, w=58)
            except Exception as ie:
                log.warning(f"Image embed failed: {ie}")

        pdf.set_xy(text_x, cur_y)

        def aline(lbl, val, col=(0,0,0)):
            if pdf.get_y() > PAGE_H - BOTTOM_MARGIN - 8:
                pdf.set_auto_page_break(True, margin=BOTTOM_MARGIN)
                pdf.add_page()
                pdf.set_auto_page_break(False)
            pdf.set_xy(text_x, pdf.get_y())
            pdf.set_font("Helvetica", "B", 8)
            pdf.set_text_color(80, 80, 80)
            pdf.cell(26, 5, safe(lbl),
                     new_x=XPos.RIGHT, new_y=YPos.TOP)
            pdf.set_font("Helvetica", "", 8)
            pdf.set_text_color(*col)
            pdf.multi_cell(text_w - 26, 5, safe(str(val)))
            pdf.set_text_color(0, 0, 0)

        # Objects
        obj_data = a.get("objects") or {}
        if obj_data.get("detected"):
            obj_items = [str(o) for o in obj_data.get("list",[])
                         if not isinstance(o, dict)]
            aline("Objects:", ", ".join(obj_items), (0,80,160))
            if obj_data.get("details"):
                aline("  Detail:", obj_data["details"])

        # Structures
        str_data = a.get("structures") or {}
        if str_data.get("detected"):
            str_items = [str(s) for s in str_data.get("list",[])
                         if not isinstance(s, dict)]
            aline("Structures:", ", ".join(str_items), (100,0,130))
            if str_data.get("details"):
                aline("  Detail:", str_data["details"])

        # Anomaly
        ano_data = a.get("anomalies") or {}
        if ano_data.get("detected"):
            aline("Anomaly:", ano_data.get("description",""), (170,60,0))

        # Seabed, water, urgency
        aline("Seabed:",   f"{sb_type}  |  Depth est: {sb_depth}")
        aline("Water:",    f"Visibility: {safe(a.get('visibility','N/A'))}  |  "
                           f"Clarity: {safe(a.get('water_clarity','N/A'))}")
        if a.get("urgency_reason"):
            aline("Urgency:", a.get("urgency_reason",""))

        # Summary bar
        sum_y = max(pdf.get_y(), cur_y + 42) + 1
        if sum_y > PAGE_H - BOTTOM_MARGIN - 8:
            pdf.set_auto_page_break(True, margin=BOTTOM_MARGIN)
            pdf.add_page()
            pdf.set_auto_page_break(False)
            sum_y = pdf.get_y() + 2

        pdf.set_xy(10, sum_y)
        pdf.set_fill_color(255, 250, 200)
        pdf.set_font("Helvetica", "I", 8)
        pdf.multi_cell(190, 5,
                       f"  Summary: {safe(a.get('one_line_summary',''))}",
                       fill=True)

        pdf.set_auto_page_break(True, margin=BOTTOM_MARGIN)
        pdf.ln(5)

    # ƒ"?ƒ"? Footer ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?
    pdf.set_font("Helvetica", "", 7)
    pdf.set_text_color(150, 150, 150)
    pdf.cell(0, 5,
             f"Generated by ROV Analyzer v4  |  "
             f"Model: {MODEL_ID}  |  "
             f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
             align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.output(output_path)
    log.info(f"PDF saved: {output_path}")
    return output_path


# ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?
# JOB DISCOVERY
# ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?

def find_latest_job():
    jobs = []
    for item in Path(OUTPUT_FOLDER).iterdir():
        if item.is_dir():
            mp = item / "job_meta.json"
            if mp.exists():
                try:
                    with open(mp) as f:
                        m = json.load(f)
                    if m.get("status") == "ready_for_analysis":
                        jobs.append((item.stat().st_mtime, str(item)))
                except Exception:
                    pass
    return sorted(jobs, reverse=True)[0][1] if jobs else None


# ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?
# MAIN
# ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?

def run_analysis(job_folder):
    log.info(f"\n{'='*55}")
    log.info(f"ROV ANALYZER v4")
    if VERIFICATION_MODE:
        log.info(f"[VERIFICATION] max {VERIFICATION_MAX_FRAMES} frames")
    log.info(f"Job: {job_folder}")
    log.info(f"{'='*55}")

    meta_path = os.path.join(job_folder, "job_meta.json")
    with open(meta_path, encoding="utf-8") as f:
        job_meta = json.load(f)

    flagged_list = job_meta.get("flagged_list", [])
    flagged_dir  = job_meta.get("flagged_dir",
                   os.path.join(job_folder, "flagged_frames"))
    total_flagged_orig = len(flagged_list)

    # Verification sampling
    if VERIFICATION_MODE and len(flagged_list) > VERIFICATION_MAX_FRAMES:
        step         = len(flagged_list) / VERIFICATION_MAX_FRAMES
        sample_idx   = [int(i*step) for i in range(VERIFICATION_MAX_FRAMES)]
        flagged_list = [flagged_list[i] for i in sample_idx]
        log.info(f"[VERIFICATION] Sampled {len(flagged_list)} of "
                 f"{total_flagged_orig} (evenly spaced)")

    log.info(f"Video:      {job_meta['video_file']}")
    log.info(f"To analyze: {len(flagged_list)} frames")

    if not flagged_list:
        send_telegram(
            f"dY¨ *ROV Analyzer ƒ?" No flagged frames*\n"
            f"dY"1 `{job_meta['video_file']}`\n\n"
            f"ƒo. Nothing to analyze. All clear."
        )
        return

    # ƒ"?ƒ"? Gemini Vision Analysis ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?
    findings = []
    for i, item in enumerate(flagged_list):
        fname      = item["frame"]
        frame_path = os.path.join(flagged_dir, fname)
        if not os.path.exists(frame_path):
            log.warning(f"Missing: {frame_path}")
            continue
        telem    = item.get("telemetry", {})
        cv_flags = item.get("cv_flags", {})
        signals  = " | ".join(cv_flags.keys()) or "general"
        log.info(f"[{i+1:3d}/{len(flagged_list)}] {fname}  [{signals}]")

        analysis = analyze_frame(frame_path, telem, cv_flags)
        urgency  = (analysis or {}).get("urgency","none")
        summary  = (analysis or {}).get("one_line_summary","")
        log.info(f"           [{urgency.upper()}] {summary}")

        findings.append({
            "frame":      fname,
            "frame_path": frame_path,
            "telemetry":  telem,
            "cv_flags":   cv_flags,
            "analysis":   analysis or {},
        })

    # ƒ"?ƒ"? Update job status ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?
    job_meta["status"]      = "analysis_complete"
    job_meta["analyzed_at"] = datetime.now().isoformat()
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(job_meta, f, indent=2, ensure_ascii=False)

    # ƒ"?ƒ"? Build summary stats ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?
    high_u  = sum(1 for f in findings if f.get("analysis",{}).get("urgency")=="high")
    med_u   = sum(1 for f in findings if f.get("analysis",{}).get("urgency")=="medium")
    all_obj = sorted({str(o) for f in findings
                      for o in f.get("analysis",{}).get("objects",{}).get("list",[])
                      if not isinstance(o, dict)})
    all_str = sorted({str(s) for f in findings
                      for s in f.get("analysis",{}).get("structures",{}).get("list",[])
                      if not isinstance(s, dict)})
    savings = job_meta["total_frames"] - len(findings)

    verify_note = (
        f"\n_[VERIFICATION] {len(findings)} of {total_flagged_orig} frames sampled._\n"
        f"_Set VERIFICATION\\_MODE = False for full run._\n"
    ) if VERIFICATION_MODE else ""

    # ƒ"?ƒ"? Telegram: analysis summary ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?
    summary_msg = (
        f"dYÿ *ROV Analysis Complete*"
        + (" *(VERIFICATION)*" if VERIFICATION_MODE else "") +
        f"\ndY"1 `{job_meta['video_file']}`\n"
        f"{verify_note}\n"
        f"dY-¬‹,? Total frames:    *{job_meta['total_frames']}*\n"
        f"dY"? OpenCV flagged:  *{total_flagged_orig}*\n"
        f"dYÿ Gemini analyzed: *{len(findings)}*\n"
        f"dY'ø API calls saved: *{savings}*\n\n"
        f"dY"' High urgency:    *{high_u}*\n"
        f"dYY­ Medium urgency:  *{med_u}*\n"
    )
    if all_obj:
        summary_msg += f"dY?ÿ Objects:    {', '.join(all_obj)}\n"
    if all_str:
        summary_msg += f"dY?-‹,? Structures:  {', '.join(all_str)}\n"
    send_telegram(summary_msg)

    # ƒ"?ƒ"? Ask approval to generate PDF ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?
    approved = wait_for_approval(
        f"dY", *Generate PDF report?*\n\n"
        f"The report will include:\n"
        f"- Summary table with all stats\n"
        f"- {len(findings)} detailed finding cards with screenshots\n"
        f"- Telemetry, urgency, AI summary per frame\n\n"
        f"ƒ?3 *Reply YES to generate and receive PDF.*\n"
        f"Reply NO to skip.\n"
        f"_(Timeout: {APPROVAL_TIMEOUT_SEC//60} min)_",
        APPROVAL_TIMEOUT_SEC
    )

    if not approved:
        log.info("PDF generation skipped.")
        return

    # ƒ"?ƒ"? Generate PDF ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?
    os.makedirs(REPORTS_FOLDER, exist_ok=True)
    verify_tag  = "_VERIFICATION" if VERIFICATION_MODE else ""
    report_name = f"ROV_Report_{job_meta['job_id']}{verify_tag}.pdf"
    report_path = os.path.join(REPORTS_FOLDER, report_name)

    log.info("Generating PDF...")
    generate_pdf(job_meta, findings, report_path)

    # ƒ"?ƒ"? Send PDF via Telegram ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?ƒ"?
    send_telegram_file(
        report_path,
        caption=f"ROV Report -- {job_meta['video_file']}"
    )
    send_telegram(
        f"ƒo. *PDF Report sent!*\n"
        f"dY"? Saved locally: `{report_path}`\n\n"
        f"Analysis complete."
    )
    log.info("Done!")


def main():
    log.info("ƒ"ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ-")
    log.info("ƒ`  ROV Analyzer v4  ƒ?"  Approval + PDF      ƒ`")
    log.info("ƒsƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?ƒ?")

    job_folder = sys.argv[1] if len(sys.argv) >= 2 else find_latest_job()
    if not job_folder:
        log.error(f"No ready jobs found in {OUTPUT_FOLDER}")
        sys.exit(1)
    log.info(f"Job: {job_folder}")
    run_analysis(job_folder)


if __name__ == "__main__":
    main()
