"""Job metadata management."""

import os
import json
import hashlib
import logging
from pathlib import Path
from datetime import datetime

log = logging.getLogger(__name__)


def create_job_id(video_path):
    """Create a unique job ID from video name + timestamp."""
    video_name = Path(video_path).stem
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{video_name}_{ts}"


def create_job_dirs(output_folder, job_id):
    """Create job directory structure. Returns (job_dir, frames_dir, flagged_dir)."""
    job_dir = os.path.join(output_folder, job_id)
    frames_dir = os.path.join(job_dir, "all_frames")
    flagged_dir = os.path.join(job_dir, "flagged_frames")
    os.makedirs(frames_dir, exist_ok=True)
    os.makedirs(flagged_dir, exist_ok=True)
    return job_dir, frames_dir, flagged_dir


def save_job_meta(job_dir, meta):
    """Save job metadata to job_meta.json."""
    meta_path = os.path.join(job_dir, "job_meta.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)
    log.info(f"Job saved: {meta_path}")
    return meta_path


def load_job_meta(job_dir):
    """Load job metadata from job_meta.json."""
    meta_path = os.path.join(job_dir, "job_meta.json")
    with open(meta_path, encoding="utf-8") as f:
        return json.load(f)


def find_latest_job(output_folder, status="ready_for_analysis"):
    """Find the most recent job with the given status."""
    jobs = []
    output = Path(output_folder)
    if not output.exists():
        return None
    for item in output.iterdir():
        if item.is_dir():
            mp = item / "job_meta.json"
            if mp.exists():
                try:
                    with open(mp) as f:
                        m = json.load(f)
                    if m.get("status") == status:
                        jobs.append((item.stat().st_mtime, str(item)))
                except Exception:
                    pass
    return sorted(jobs, reverse=True)[0][1] if jobs else None


def list_jobs(output_folder):
    """List all jobs with their metadata. Returns list of (job_dir, meta) tuples."""
    jobs = []
    output = Path(output_folder)
    if not output.exists():
        return jobs
    for item in sorted(output.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True):
        if item.is_dir():
            mp = item / "job_meta.json"
            if mp.exists():
                try:
                    with open(mp) as f:
                        meta = json.load(f)
                    jobs.append((str(item), meta))
                except Exception:
                    pass
    return jobs


def hash_video_header(video_path, size=65536):
    """Hash first bytes of video for duplicate detection."""
    return hashlib.md5(open(video_path, "rb").read(size)).hexdigest()
