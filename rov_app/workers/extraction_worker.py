"""QThread worker for Stage 1: frame extraction + OpenCV analysis + deduplication."""

import os
import logging
from datetime import datetime
from PySide6.QtCore import QThread, Signal

from rov_app.core.frame_extractor import extract_frames
from rov_app.core.opencv_analyzer import OpenCVAnalyzer
from rov_app.core.annotations import draw_cv_annotations
from rov_app.core.deduplicator import FrameDeduplicator
from rov_app.core.telemetry import load_telemetry, get_telemetry_at
from rov_app.core.job import create_job_id, create_job_dirs, save_job_meta

log = logging.getLogger(__name__)


class ExtractionWorker(QThread):
    """Runs the full Stage 1 pipeline in a background thread."""

    # Signals
    progress = Signal(int, int, str)       # (current, total, status_text)
    frame_processed = Signal(dict)         # Per-frame result for live UI update
    finished = Signal(dict)                # job_meta on completion
    error = Signal(str)                    # Error message

    def __init__(self, video_path, config):
        super().__init__()
        self.video_path = video_path
        self.config = config

    def run(self):
        try:
            self._run_pipeline()
        except Exception as e:
            log.exception("Extraction worker error")
            self.error.emit(str(e))

    def _run_pipeline(self):
        video_path = self.video_path
        cfg = self.config

        output_folder = cfg.get("folders", "output_folder")
        every_n_sec = cfg.get("extraction", "frame_every_sec", default=5)
        thresholds = cfg.get_opencv_thresholds()
        dedup_enabled = cfg.get("extraction", "dedup_enabled", default=True)
        dedup_threshold = cfg.get("extraction", "dedup_threshold", default=0.5)

        if not output_folder:
            self.error.emit("Output folder not configured. Please set it in Settings.")
            return

        # Create job
        job_id = create_job_id(video_path)
        job_dir, frames_dir, flagged_dir = create_job_dirs(output_folder, job_id)
        self.progress.emit(0, 1, "Extracting frames...")

        # Load telemetry
        telemetry, sub_path = load_telemetry(video_path)

        # Extract frames
        frames = extract_frames(video_path, frames_dir, every_n_sec)
        if not frames:
            self.error.emit("No frames extracted. Check that ffmpeg is installed and on PATH.")
            return

        total = len(frames)
        self.progress.emit(0, total, f"Analyzing {total} frames with OpenCV...")

        # OpenCV analysis
        analyzer = OpenCVAnalyzer(thresholds)
        stage1_results = []
        flagged_list = []
        skipped_count = 0

        for i, frame_path in enumerate(frames):
            if self.isInterruptionRequested():
                self.error.emit("Cancelled by user.")
                return

            fname = os.path.basename(frame_path)
            telem = get_telemetry_at(i, telemetry, every_n_sec)
            flags = analyzer.analyze(frame_path)
            skipped = "skip" in flags or "error" in flags
            flagged = not skipped and len(flags) > 0

            result = {
                "frame": fname,
                "frame_idx": i,
                "timestamp": telem.get("timestamp", "00:00:00"),
                "telemetry": telem,
                "cv_flags": flags,
                "flagged": flagged,
                "skipped": skipped,
            }
            stage1_results.append(result)

            if flagged:
                flagged_path = os.path.join(flagged_dir, fname)
                draw_cv_annotations(frame_path, flags, flagged_path)
                result["frame_path"] = flagged_path
                flagged_list.append(result)
            elif not skipped:
                result["frame_path"] = frame_path
            else:
                skipped_count += 1

            self.frame_processed.emit(result)
            self.progress.emit(i + 1, total, f"OpenCV: {i + 1}/{total}")

        # Deduplication
        dup_count = 0
        if dedup_enabled and flagged_list:
            self.progress.emit(0, len(flagged_list), "Removing duplicate frames...")
            dedup = FrameDeduplicator(dedup_threshold)
            flagged_list, dup_count = dedup.deduplicate(
                flagged_list,
                on_progress=lambda c, t: self.progress.emit(c, t, f"Dedup: {c}/{t}")
            )

        flagged_count = len(flagged_list)
        clear_count = total - flagged_count - skipped_count - dup_count

        # Save job metadata
        meta = {
            "job_id": job_id,
            "video_file": os.path.basename(video_path),
            "video_path": video_path,
            "subtitle_path": sub_path,
            "created_at": datetime.now().isoformat(),
            "total_frames": total,
            "flagged_count": flagged_count,
            "clear_count": clear_count,
            "skipped_count": skipped_count,
            "duplicate_count": dup_count,
            "frame_interval_sec": every_n_sec,
            "job_dir": job_dir,
            "flagged_dir": flagged_dir,
            "stage1_results": stage1_results,
            "flagged_list": flagged_list,
            "status": "ready_for_analysis",
        }
        save_job_meta(job_dir, meta)
        self.progress.emit(total, total, "Extraction complete!")
        self.finished.emit(meta)
