"""QThread worker for Stage 2: AI vision analysis."""

import os
import logging
from datetime import datetime
from PySide6.QtCore import QThread, Signal

from rov_app.ai import get_provider
from rov_app.core.annotations import draw_ai_detections
from rov_app.core.job import save_job_meta

log = logging.getLogger(__name__)


class AnalysisWorker(QThread):
    """Runs AI analysis on flagged frames in a background thread."""

    progress = Signal(int, int, str)       # (current, total, status_text)
    frame_analyzed = Signal(int, dict)     # (index, finding_dict)
    finished = Signal(list)                # all findings
    error = Signal(str)

    def __init__(self, job_meta, config):
        super().__init__()
        self.job_meta = job_meta
        self.config = config

    def run(self):
        try:
            self._run_analysis()
        except Exception as e:
            log.exception("Analysis worker error")
            self.error.emit(str(e))

    def _run_analysis(self):
        cfg = self.config
        meta = self.job_meta

        provider_name = cfg.get("ai", "provider", default="openrouter")
        api_key = cfg.get("ai", "api_key", default="")
        model_id = cfg.get("ai", "model_id", default="google/gemini-2.5-flash-lite")
        max_tokens = cfg.get("ai", "max_tokens", default=700)
        enable_detection = cfg.get("ai", "enable_object_detection", default=False)
        detection_mode = cfg.get("ai", "detection_mode", default="precise")
        verification_mode = cfg.get("ai", "verification_mode", default=False)
        max_verify_frames = cfg.get("ai", "verification_max_frames", default=20)

        if not api_key:
            self.error.emit(f"No API key configured for {provider_name}. Please set it in Settings.")
            return

        provider = get_provider(provider_name)
        flagged_list = meta.get("flagged_list", [])
        flagged_dir = meta.get("flagged_dir", "")

        # Verification sampling
        total_flagged_orig = len(flagged_list)
        if verification_mode and len(flagged_list) > max_verify_frames:
            step = len(flagged_list) / max_verify_frames
            sample_idx = [int(i * step) for i in range(max_verify_frames)]
            flagged_list = [flagged_list[i] for i in sample_idx]

        total = len(flagged_list)
        if total == 0:
            self.finished.emit([])
            return

        self.progress.emit(0, total, f"Analyzing 0/{total} frames...")

        findings = []
        for i, item in enumerate(flagged_list):
            if self.isInterruptionRequested():
                self.error.emit("Cancelled by user.")
                return

            fname = item["frame"]
            frame_path = item.get("frame_path", os.path.join(flagged_dir, fname))
            if not os.path.exists(frame_path):
                log.warning(f"Missing: {frame_path}")
                continue

            telem = item.get("telemetry", {})
            cv_flags = item.get("cv_flags", {})

            self.progress.emit(i, total, f"Analyzing {i + 1}/{total}: {fname}")

            analysis = provider.analyze_frame(
                frame_path, telem, cv_flags,
                api_key, model_id, max_tokens,
                enable_detection, detection_mode
            )

            finding = {
                "frame": fname,
                "frame_path": frame_path,
                "telemetry": telem,
                "cv_flags": cv_flags,
                "analysis": analysis or {},
            }

            # Draw AI detection annotations if enabled
            if enable_detection and analysis.get("detections"):
                detected_path = frame_path.replace(".jpg", "_detected.jpg")
                draw_ai_detections(frame_path, analysis["detections"], detected_path, detection_mode)
                finding["detected_frame_path"] = detected_path

            findings.append(finding)
            self.frame_analyzed.emit(i, finding)

        # Update job status
        meta["status"] = "analysis_complete"
        meta["analyzed_at"] = datetime.now().isoformat()
        meta["model_id"] = model_id
        meta["provider"] = provider_name
        job_dir = meta.get("job_dir", "")
        if job_dir:
            save_job_meta(job_dir, meta)

        self.progress.emit(total, total, "Analysis complete!")
        self.finished.emit(findings)
