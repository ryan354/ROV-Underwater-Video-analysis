"""Frame extraction from video files using ffmpeg."""

import os
import sys
import logging
import subprocess
import shutil
from pathlib import Path

log = logging.getLogger(__name__)


def _find_tool(name):
    """Find ffmpeg/ffprobe: check bundled folder first, then PATH."""
    # Check bundled folder (for PyInstaller builds)
    if getattr(sys, 'frozen', False):
        app_dir = os.path.dirname(sys.executable)
    else:
        app_dir = str(Path(__file__).parent.parent.parent)
    bundled = os.path.join(app_dir, "ffmpeg", f"{name}.exe")
    if os.path.exists(bundled):
        log.debug(f"Using bundled {name}: {bundled}")
        return bundled
    # Fallback to PATH
    found = shutil.which(name)
    if found:
        return found
    return name  # let subprocess raise the error


def extract_frames(video_path, out_dir, every_n_sec=5, on_progress=None):
    """
    Extract frames from a video file using ffmpeg.

    Args:
        video_path: Path to the video file
        out_dir: Directory to save extracted frames
        every_n_sec: Extract one frame every N seconds
        on_progress: Optional callback(current, total) for progress reporting
    Returns:
        List of frame file paths
    """
    os.makedirs(out_dir, exist_ok=True)
    pattern = os.path.join(out_dir, "frame_%05d.jpg")
    cmd = [
        _find_tool("ffmpeg"), "-i", video_path,
        "-vf", f"fps=1/{every_n_sec}",
        "-q:v", "2", "-y", pattern
    ]
    log.info(f"Extracting 1 frame every {every_n_sec}s...")

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        log.error(f"ffmpeg error:\n{result.stderr[-400:]}")
        return []

    frames = sorted(Path(out_dir).glob("frame_*.jpg"))
    total = len(frames)
    log.info(f"Extracted {total} frames.")

    if on_progress and total > 0:
        on_progress(total, total)

    return [str(f) for f in frames]


def get_video_duration(video_path):
    """Get video duration in seconds using ffprobe."""
    try:
        cmd = [
            _find_tool("ffprobe"), "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            video_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            return float(result.stdout.strip())
    except Exception:
        pass
    return 0
