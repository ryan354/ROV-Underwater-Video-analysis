"""Telemetry parsing from subtitle/CSV files."""

import os
import re
import csv
import logging
from pathlib import Path

log = logging.getLogger(__name__)


def find_subtitle_file(video_path):
    """Find a telemetry file adjacent to the video."""
    base = Path(video_path).stem
    folder = Path(video_path).parent
    for ext in [".srt", ".txt", ".csv", ".vtt", ".ass"]:
        c = folder / (base + ext)
        if c.exists():
            log.info(f"Telemetry: {c.name}")
            return str(c)
    log.info("No telemetry file found.")
    return None


def parse_telemetry_srt(srt_path):
    """Parse SRT subtitle file for telemetry data."""
    telemetry = []
    if not srt_path or not os.path.exists(srt_path):
        return telemetry
    with open(srt_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    for block in re.split(r"\n\n+", content.strip()):
        lines = block.strip().split("\n")
        if len(lines) < 3:
            continue
        ts = re.match(r"(\d+:\d+:\d+),\d+", lines[1]) if len(lines) > 1 else None
        timestamp = ts.group(1) if ts else "00:00:00"
        text = " ".join(lines[2:])
        entry = {"timestamp": timestamp, "raw": text}
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
                            except Exception:
                                pass
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
        if not events:
            return telemetry
        for line in events.group(1).strip().split("\n"):
            if not line.startswith("Dialogue:"):
                continue
            parts = line[9:].split(",", 9)
            if len(parts) < 10:
                continue
            ts = parts[1].strip()[:8]
            txt = parts[9].strip()
            entry = {"timestamp": ts, "raw": txt}
            for key, pat in [
                ("altitude", r"[Aa]lt[:\s]+([+-]?\d+\.?\d*)"),
                ("depth",    r"[Dd]epth[:\s]+([+-]?\d+\.?\d*)"),
                ("pitch",    r"[Pp]itch[:\s]+([+-]?\d+\.?\d*)"),
                ("roll",     r"[Rr]oll[:\s]+([+-]?\d+\.?\d*)"),
                ("speed",    r"[Ss]peed[:\s]+([+-]?\d+\.?\d*)"),
                ("heading",  r"[Hh]ead[:\s]+([+-]?\d+\.?\d*)"),
                ("temp",     r"[Tt]emp[:\s]+([+-]?\d+\.?\d*)"),
            ]:
                m = re.search(pat, txt)
                if m:
                    entry[key] = float(m.group(1))
            telemetry.append(entry)
        log.info(f"Parsed {len(telemetry)} ASS entries.")
    except Exception as e:
        log.warning(f"ASS error: {e}")
    return telemetry


def load_telemetry(video_path):
    """Load telemetry from any supported file adjacent to the video."""
    sub_path = find_subtitle_file(video_path)
    if not sub_path:
        return [], None
    ext = os.path.splitext(sub_path)[1].lower()
    if ext == ".csv":
        return parse_telemetry_csv(sub_path), sub_path
    if ext in [".ass", ".ssa"]:
        return parse_telemetry_ass(sub_path), sub_path
    return parse_telemetry_srt(sub_path), sub_path


def get_telemetry_at(frame_index, telemetry, every_n_sec):
    """Find the telemetry entry closest to a given frame's timestamp."""
    frame_sec = frame_index * every_n_sec
    h, m, s = frame_sec // 3600, (frame_sec % 3600) // 60, frame_sec % 60
    best = {"timestamp": f"{h:02d}:{m:02d}:{s:02d}"}
    best_diff = float("inf")
    for entry in telemetry:
        try:
            p = entry["timestamp"].split(":")
            esec = int(p[0]) * 3600 + int(p[1]) * 60 + int(p[2])
            diff = abs(esec - frame_sec)
            if diff < best_diff:
                best_diff = diff
                best = entry
        except Exception:
            continue
    return best


def fmt_telemetry(t):
    """Format telemetry dict as a display string."""
    units = {"depth": "m", "altitude": "m", "pitch": "deg",
             "roll": "deg", "speed": "kn", "heading": "deg", "temp": "C"}
    parts = [f"{k.capitalize()}: {t[k]}{u}" for k, u in units.items() if k in t]
    return "  |  ".join(parts) or f"Timestamp: {t.get('timestamp', 'N/A')}"


def fmt_flags(flags):
    """Format CV flags dict as a display string."""
    return "  |  ".join(
        f"{n.upper()}: {i.get('reason', '')}" for n, i in flags.items()
    ) if flags else "General interest"
