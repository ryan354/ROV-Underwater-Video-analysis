"""Main application window for ROV Underwater Analyzer."""

import os
import subprocess
import platform
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QLabel, QPushButton, QGroupBox, QFormLayout, QProgressBar,
    QComboBox, QSpinBox, QCheckBox, QFileDialog, QMessageBox,
    QStatusBar, QMenuBar, QListWidget, QListWidgetItem, QDoubleSpinBox
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QAction

from rov_app.core.config import ConfigManager
from rov_app.core.job import list_jobs, load_job_meta
from rov_app.core.constants import SUPPORTED_EXTS
from rov_app.workers.extraction_worker import ExtractionWorker
from rov_app.workers.analysis_worker import AnalysisWorker
from rov_app.workers.pdf_worker import PDFWorker
from rov_app.ui.frame_grid_widget import FrameGridWidget
from rov_app.ui.settings_dialog import SettingsDialog, PROVIDER_MODELS
from rov_app.ui.frame_detail_dialog import FrameDetailDialog


class MainWindow(QMainWindow):
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.current_meta = None
        self.current_findings = None
        self.extraction_worker = None
        self.analysis_worker = None
        self.pdf_worker = None

        self.setWindowTitle("ROV Underwater Analyzer")
        self.setMinimumSize(1100, 700)
        self.resize(1280, 800)

        self._build_menu()
        self._build_ui()
        self._build_statusbar()
        self._refresh_job_history()
        self._update_button_states()

    # ─── Menu ────────────────────────────────────────────────────

    def _build_menu(self):
        menubar = self.menuBar()

        file_menu = menubar.addMenu("File")
        open_action = QAction("Open Video...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self._open_video)
        file_menu.addAction(open_action)
        file_menu.addSeparator()
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        settings_menu = menubar.addMenu("Settings")
        prefs_action = QAction("Preferences...", self)
        prefs_action.setShortcut("Ctrl+,")
        prefs_action.triggered.connect(self._open_settings)
        settings_menu.addAction(prefs_action)

        help_menu = menubar.addMenu("Help")
        about_action = QAction("About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    # ─── UI Layout ───────────────────────────────────────────────

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)

        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)

        # ── Left Sidebar ──
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(310)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(10, 10, 10, 10)
        sidebar_layout.setSpacing(8)

        # Open video button
        open_btn = QPushButton("Open Video...")
        open_btn.setObjectName("primaryBtn")
        open_btn.clicked.connect(self._open_video)
        sidebar_layout.addWidget(open_btn)

        # Video info
        self.video_info_group = QGroupBox("Video Info")
        vi_layout = QFormLayout(self.video_info_group)
        self.video_name_label = QLabel("No video loaded")
        self.video_name_label.setWordWrap(True)
        vi_layout.addRow("File:", self.video_name_label)
        self.video_telemetry_label = QLabel("-")
        vi_layout.addRow("Telemetry:", self.video_telemetry_label)
        sidebar_layout.addWidget(self.video_info_group)

        # Job stats
        self.stats_group = QGroupBox("Job Statistics")
        stats_layout = QFormLayout(self.stats_group)
        self.stat_total = QLabel("-")
        self.stat_flagged = QLabel("-")
        self.stat_clear = QLabel("-")
        self.stat_skipped = QLabel("-")
        self.stat_dedup = QLabel("-")
        stats_layout.addRow("Total Frames:", self.stat_total)
        stats_layout.addRow("Flagged:", self.stat_flagged)
        stats_layout.addRow("Clear:", self.stat_clear)
        stats_layout.addRow("Skipped:", self.stat_skipped)
        stats_layout.addRow("Duplicates:", self.stat_dedup)
        sidebar_layout.addWidget(self.stats_group)

        # Quick options
        opts_group = QGroupBox("Quick Options")
        opts_layout = QFormLayout(opts_group)

        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(1, 30)
        self.interval_spin.setValue(self.config.get("extraction", "frame_every_sec", default=5))
        self.interval_spin.setSuffix(" sec")
        opts_layout.addRow("Frame Interval:", self.interval_spin)

        self.dedup_check = QCheckBox("Remove duplicates")
        self.dedup_check.setChecked(self.config.get("extraction", "dedup_enabled", default=True))
        opts_layout.addRow(self.dedup_check)

        self.detect_check = QCheckBox("Object detection")
        self.detect_check.setChecked(self.config.get("ai", "enable_object_detection", default=False))
        opts_layout.addRow(self.detect_check)

        self.verify_check = QCheckBox("Verification mode")
        self.verify_check.setChecked(self.config.get("ai", "verification_mode", default=False))
        opts_layout.addRow(self.verify_check)

        sidebar_layout.addWidget(opts_group)

        # Action buttons
        ctrl_group = QGroupBox("Actions")
        ctrl_layout = QVBoxLayout(ctrl_group)

        self.extract_btn = QPushButton("1. Extract & Analyze Frames")
        self.extract_btn.setObjectName("primaryBtn")
        self.extract_btn.clicked.connect(self._start_extraction)
        ctrl_layout.addWidget(self.extract_btn)

        self.analyze_btn = QPushButton("2. Run AI Analysis")
        self.analyze_btn.clicked.connect(self._start_analysis)
        ctrl_layout.addWidget(self.analyze_btn)

        self.pdf_btn = QPushButton("3. Generate PDF Report")
        self.pdf_btn.clicked.connect(self._start_pdf)
        ctrl_layout.addWidget(self.pdf_btn)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setObjectName("dangerBtn")
        self.cancel_btn.clicked.connect(self._cancel_worker)
        self.cancel_btn.hide()
        ctrl_layout.addWidget(self.cancel_btn)

        sidebar_layout.addWidget(ctrl_group)

        # Job history
        history_group = QGroupBox("Job History")
        history_layout = QVBoxLayout(history_group)
        self.job_list = QListWidget()
        self.job_list.itemDoubleClicked.connect(self._load_job_from_history)
        history_layout.addWidget(self.job_list)
        sidebar_layout.addWidget(history_group)

        sidebar_layout.addStretch()
        splitter.addWidget(sidebar)

        # ── Center Panel ──
        center = QWidget()
        center_layout = QVBoxLayout(center)
        center_layout.setContentsMargins(10, 10, 10, 10)
        center_layout.setSpacing(8)

        # Stage 1 section
        s1_group = QGroupBox("Stage 1: Frame Extraction & OpenCV Analysis")
        s1_layout = QVBoxLayout(s1_group)

        self.s1_progress = QProgressBar()
        self.s1_progress.setFormat("%v/%m - %p%")
        s1_layout.addWidget(self.s1_progress)

        self.s1_status = QLabel("Ready. Open a video to start.")
        self.s1_status.setObjectName("statusLabel")
        s1_layout.addWidget(self.s1_status)

        self.frame_grid = FrameGridWidget()
        self.frame_grid.frame_clicked.connect(self._show_frame_detail)
        s1_layout.addWidget(self.frame_grid)

        center_layout.addWidget(s1_group, stretch=2)

        # Stage 2 section
        s2_group = QGroupBox("Stage 2: AI Analysis & Report")
        s2_layout = QVBoxLayout(s2_group)

        # Provider/model row
        ai_row = QHBoxLayout()
        ai_row.addWidget(QLabel("Provider:"))
        self.ai_provider_combo = QComboBox()
        self.ai_provider_combo.addItems(["openrouter", "openai", "anthropic"])
        self.ai_provider_combo.setCurrentText(self.config.get("ai", "provider", default="openrouter"))
        self.ai_provider_combo.currentTextChanged.connect(self._on_provider_changed)
        ai_row.addWidget(self.ai_provider_combo)
        ai_row.addWidget(QLabel("Model:"))
        self.ai_model_edit = QComboBox()
        self.ai_model_edit.setEditable(True)
        self.ai_model_edit.setMinimumWidth(250)
        self._on_provider_changed(self.ai_provider_combo.currentText())
        self.ai_model_edit.setCurrentText(self.config.get("ai", "model_id", default="google/gemini-2.5-flash-lite"))
        ai_row.addWidget(self.ai_model_edit)
        ai_row.addStretch()
        s2_layout.addLayout(ai_row)

        self.s2_progress = QProgressBar()
        self.s2_progress.setFormat("%v/%m - %p%")
        s2_layout.addWidget(self.s2_progress)

        self.s2_status = QLabel("Waiting for Stage 1 to complete.")
        self.s2_status.setObjectName("statusLabel")
        s2_layout.addWidget(self.s2_status)

        # Results row
        results_row = QHBoxLayout()
        self.result_label = QLabel("")
        self.result_label.setWordWrap(True)
        results_row.addWidget(self.result_label)
        s2_layout.addLayout(results_row)

        # Report options row
        report_row = QHBoxLayout()
        report_row.addWidget(QLabel("Report:"))
        self.detect_report_check = QCheckBox("Include detection overlays")
        self.detect_report_check.setChecked(self.config.get("ai", "enable_object_detection", default=False))
        report_row.addWidget(self.detect_report_check)
        report_row.addStretch()
        s2_layout.addLayout(report_row)

        center_layout.addWidget(s2_group, stretch=1)
        splitter.addWidget(center)
        splitter.setSizes([270, 900])

    def _build_statusbar(self):
        self.statusBar().showMessage("Ready")

    def _on_provider_changed(self, provider):
        """Update model dropdown when provider changes."""
        self.ai_model_edit.clear()
        models = PROVIDER_MODELS.get(provider, [])
        self.ai_model_edit.addItems(models)

    # ─── Actions ─────────────────────────────────────────────────

    def _open_video(self):
        exts = " ".join(f"*{e}" for e in SUPPORTED_EXTS)
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Video File", "",
            f"Video Files ({exts});;All Files (*)"
        )
        if path:
            self.video_path = path
            self.video_name_label.setText(os.path.basename(path))
            self.video_telemetry_label.setText("Will detect on extraction")
            self.frame_grid.clear()
            self.current_meta = None
            self.current_findings = None
            self._update_button_states()
            self.s1_status.setText(f"Video loaded: {os.path.basename(path)}")
            self.statusBar().showMessage(f"Loaded: {path}")

    def _open_settings(self):
        dlg = SettingsDialog(self.config, self)
        if dlg.exec():
            # Refresh ALL UI widgets with new settings
            self.interval_spin.setValue(self.config.get("extraction", "frame_every_sec", default=5))
            self.dedup_check.setChecked(self.config.get("extraction", "dedup_enabled", default=True))
            self.detect_check.setChecked(self.config.get("ai", "enable_object_detection", default=False))
            self.verify_check.setChecked(self.config.get("ai", "verification_mode", default=False))
            self.ai_provider_combo.setCurrentText(self.config.get("ai", "provider", default="openrouter"))
            self.ai_model_edit.setCurrentText(self.config.get("ai", "model_id", default=""))
            self.detect_report_check.setChecked(self.config.get("ai", "enable_object_detection", default=False))

    def _show_about(self):
        QMessageBox.about(self, "About ROV Analyzer",
                          "ROV Underwater Video Analyzer v1.0\n\n"
                          "Automated underwater inspection using\n"
                          "OpenCV + AI vision analysis.\n\n"
                          "Built with PySide6 (Qt)")

    def _update_button_states(self):
        has_video = hasattr(self, 'video_path') and bool(self.video_path)
        has_meta = self.current_meta is not None
        has_findings = self.current_findings is not None
        working = bool(
            (self.extraction_worker and self.extraction_worker.isRunning()) or
            (self.analysis_worker and self.analysis_worker.isRunning()) or
            (self.pdf_worker and self.pdf_worker.isRunning())
        )

        self.extract_btn.setEnabled(has_video and not working)
        self.analyze_btn.setEnabled(has_meta and not working)
        self.pdf_btn.setEnabled(has_findings and not working)
        self.cancel_btn.setVisible(working)

    def _cancel_worker(self):
        for worker in [self.extraction_worker, self.analysis_worker, self.pdf_worker]:
            if worker and worker.isRunning():
                worker.requestInterruption()

    # ─── Stage 1: Extraction ─────────────────────────────────────

    def _start_extraction(self):
        if not hasattr(self, 'video_path') or not self.video_path:
            return

        # Apply quick options to config
        self.config.set("extraction", "frame_every_sec", self.interval_spin.value())
        self.config.set("extraction", "dedup_enabled", self.dedup_check.isChecked())
        self.config.set("ai", "enable_object_detection", self.detect_check.isChecked())
        self.config.set("ai", "verification_mode", self.verify_check.isChecked())

        if not self.config.get("folders", "output_folder"):
            QMessageBox.warning(self, "No Output Folder",
                                "Please set an output folder in Settings first.")
            self._open_settings()
            return

        self.frame_grid.clear()
        self.current_meta = None
        self.current_findings = None
        self.s1_progress.setValue(0)
        self.s1_status.setText("Starting extraction...")

        self.extraction_worker = ExtractionWorker(self.video_path, self.config)
        self.extraction_worker.progress.connect(self._on_extraction_progress)
        self.extraction_worker.frame_processed.connect(self._on_frame_processed)
        self.extraction_worker.finished.connect(self._on_extraction_done)
        self.extraction_worker.error.connect(self._on_worker_error)
        self.extraction_worker.start()
        self._update_button_states()

    def _on_extraction_progress(self, current, total, text):
        self.s1_progress.setMaximum(total)
        self.s1_progress.setValue(current)
        self.s1_status.setText(text)

    def _on_frame_processed(self, result):
        self.frame_grid.add_frame(result)

    def _on_extraction_done(self, meta):
        self.current_meta = meta
        self.s1_status.setText(
            f"Done! {meta['total_frames']} frames | "
            f"{meta['flagged_count']} flagged | "
            f"{meta.get('duplicate_count', 0)} duplicates removed"
        )
        self.stat_total.setText(str(meta['total_frames']))
        self.stat_flagged.setText(str(meta['flagged_count']))
        self.stat_clear.setText(str(meta['clear_count']))
        self.stat_skipped.setText(str(meta['skipped_count']))
        self.stat_dedup.setText(str(meta.get('duplicate_count', 0)))
        self.video_telemetry_label.setText(
            os.path.basename(meta['subtitle_path']) if meta.get('subtitle_path') else "None"
        )
        self.statusBar().showMessage(f"Stage 1 complete: {meta['job_id']}")
        self.s2_status.setText("Ready for AI analysis. Click 'Run AI Analysis'.")
        self._refresh_job_history()
        self._update_button_states()

    # ─── Stage 2: AI Analysis ────────────────────────────────────

    def _start_analysis(self):
        if not self.current_meta:
            return

        # Sync provider/model from UI
        self.config.set("ai", "provider", self.ai_provider_combo.currentText())
        self.config.set("ai", "model_id", self.ai_model_edit.currentText())
        self.config.set("ai", "enable_object_detection", self.detect_check.isChecked())
        self.config.set("ai", "verification_mode", self.verify_check.isChecked())

        if not self.config.get("ai", "api_key"):
            QMessageBox.warning(self, "No API Key",
                                f"Please set your {self.ai_provider_combo.currentText()} API key in Settings.")
            self._open_settings()
            return

        self.current_findings = None
        self.s2_progress.setValue(0)
        self.s2_status.setText("Starting AI analysis...")
        self.result_label.setText("")

        self.analysis_worker = AnalysisWorker(self.current_meta, self.config)
        self.analysis_worker.progress.connect(self._on_analysis_progress)
        self.analysis_worker.frame_analyzed.connect(self._on_frame_analyzed)
        self.analysis_worker.finished.connect(self._on_analysis_done)
        self.analysis_worker.error.connect(self._on_worker_error)
        self.analysis_worker.start()
        self._update_button_states()

    def _on_analysis_progress(self, current, total, text):
        self.s2_progress.setMaximum(total)
        self.s2_progress.setValue(current)
        self.s2_status.setText(text)

    def _on_frame_analyzed(self, idx, finding):
        analysis = finding.get("analysis", {})
        self.frame_grid.update_frame_analysis(finding.get("frame", ""), analysis)

    def _on_analysis_done(self, findings):
        self.current_findings = findings

        # Build summary
        high = sum(1 for f in findings if f.get("analysis", {}).get("urgency") == "high")
        med = sum(1 for f in findings if f.get("analysis", {}).get("urgency") == "medium")
        low = sum(1 for f in findings if f.get("analysis", {}).get("urgency") == "low")
        objs = sorted({str(o) for f in findings
                        for o in f.get("analysis", {}).get("objects", {}).get("list", [])
                        if not isinstance(o, dict)})

        self.s2_status.setText(f"Analysis complete! {len(findings)} frames analyzed.")
        summary = f"Urgency: {high} high, {med} medium, {low} low"
        if objs:
            summary += f"\nObjects: {', '.join(objs[:10])}"
        self.result_label.setText(summary)
        self.statusBar().showMessage("Stage 2 complete. Ready to generate PDF.")
        self._update_button_states()

    # ─── PDF Generation ──────────────────────────────────────────

    def _start_pdf(self):
        if not self.current_meta or not self.current_findings:
            return

        if not self.config.get("folders", "reports_folder"):
            QMessageBox.warning(self, "No Reports Folder",
                                "Please set a reports folder in Settings first.")
            self._open_settings()
            return

        # Sync report options from UI
        self.config.set("ai", "enable_object_detection", self.detect_report_check.isChecked())

        self.s2_status.setText("Generating PDF report...")

        self.pdf_worker = PDFWorker(self.current_meta, self.current_findings, self.config)
        self.pdf_worker.progress.connect(lambda t: self.s2_status.setText(t))
        self.pdf_worker.finished.connect(self._on_pdf_done)
        self.pdf_worker.error.connect(self._on_worker_error)
        self.pdf_worker.start()
        self._update_button_states()

    def _on_pdf_done(self, paths):
        names = [os.path.basename(p) for p in paths]
        self.s2_status.setText(f"PDF generated: {', '.join(names)}")
        self.statusBar().showMessage(f"Reports saved: {', '.join(names)}")
        self._update_button_states()

        # Open the first PDF
        if paths and os.path.exists(paths[0]):
            if platform.system() == "Windows":
                os.startfile(paths[0])
            elif platform.system() == "Darwin":
                subprocess.run(["open", paths[0]])
            else:
                subprocess.run(["xdg-open", paths[0]])

    # ─── Common ──────────────────────────────────────────────────

    def _on_worker_error(self, msg):
        QMessageBox.critical(self, "Error", msg)
        self.statusBar().showMessage(f"Error: {msg}")
        self.s1_status.setText(f"Error: {msg}")
        self._update_button_states()

    def _show_frame_detail(self, data):
        dlg = FrameDetailDialog(data, self)
        dlg.exec()

    # ─── Job History ─────────────────────────────────────────────

    def _refresh_job_history(self):
        self.job_list.clear()
        output_folder = self.config.get("folders", "output_folder", default="")
        if not output_folder:
            return
        for job_dir, meta in list_jobs(output_folder)[:20]:
            status = meta.get("status", "?")
            icon = {"ready_for_analysis": "[READY]", "analysis_complete": "[DONE]"}.get(status, "[?]")
            text = f"{icon} {meta.get('job_id', os.path.basename(job_dir))}"
            item = QListWidgetItem(text)
            item.setData(Qt.UserRole, job_dir)
            self.job_list.addItem(item)

    def _load_job_from_history(self, item):
        job_dir = item.data(Qt.UserRole)
        try:
            meta = load_job_meta(job_dir)
            self.current_meta = meta
            self.current_findings = None
            self.video_path = meta.get("video_path", "")
            self.video_name_label.setText(meta.get("video_file", "?"))
            self.stat_total.setText(str(meta.get("total_frames", "-")))
            self.stat_flagged.setText(str(meta.get("flagged_count", "-")))
            self.stat_clear.setText(str(meta.get("clear_count", "-")))
            self.stat_skipped.setText(str(meta.get("skipped_count", "-")))
            self.stat_dedup.setText(str(meta.get("duplicate_count", "-")))

            # Populate frame grid from meta
            self.frame_grid.clear()
            for result in meta.get("stage1_results", []):
                # Resolve frame path
                if result.get("flagged"):
                    result["frame_path"] = os.path.join(
                        meta.get("flagged_dir", ""), result["frame"])
                else:
                    result["frame_path"] = os.path.join(
                        meta.get("job_dir", ""), "all_frames", result["frame"])
                self.frame_grid.add_frame(result)

            self.s1_status.setText(f"Loaded job: {meta['job_id']}")
            self.s2_status.setText("Ready for AI analysis." if meta.get("status") == "ready_for_analysis"
                                   else "Analysis complete. Generate PDF or re-analyze.")
            self.statusBar().showMessage(f"Loaded: {meta['job_id']}")
            self._update_button_states()
        except Exception as e:
            QMessageBox.warning(self, "Load Error", f"Could not load job: {e}")
