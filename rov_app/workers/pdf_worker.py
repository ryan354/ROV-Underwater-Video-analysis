"""QThread worker for PDF report generation."""

import os
import logging
from PySide6.QtCore import QThread, Signal

from rov_app.core.pdf_generator import generate_pdf

log = logging.getLogger(__name__)


class PDFWorker(QThread):
    """Generates PDF report in a background thread."""

    progress = Signal(str)       # Status text
    finished = Signal(list)      # List of generated PDF paths
    error = Signal(str)

    def __init__(self, job_meta, findings, config):
        super().__init__()
        self.job_meta = job_meta
        self.findings = findings
        self.config = config

    def run(self):
        try:
            self._generate()
        except Exception as e:
            log.exception("PDF worker error")
            self.error.emit(str(e))

    def _generate(self):
        cfg = self.config
        meta = self.job_meta
        findings = self.findings

        reports_folder = cfg.get("folders", "reports_folder", default="")
        model_name = cfg.get("ai", "model_id", default="")
        verification_mode = cfg.get("ai", "verification_mode", default=False)
        include_detections = cfg.get("ai", "enable_object_detection", default=False)

        if not reports_folder:
            self.error.emit("Reports folder not configured. Please set it in Settings.")
            return

        os.makedirs(reports_folder, exist_ok=True)

        verify_tag = "_VERIFICATION" if verification_mode else ""
        report_name = f"ROV_Report_{meta['job_id']}{verify_tag}.pdf"
        report_path = os.path.join(reports_folder, report_name)

        self.progress.emit("Generating PDF report...")

        generate_pdf(
            meta, findings, report_path,
            model_name=model_name,
            include_detections=include_detections,
            verification_mode=verification_mode,
        )

        self.finished.emit([report_path])
