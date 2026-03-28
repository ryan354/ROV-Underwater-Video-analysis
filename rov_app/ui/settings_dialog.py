"""Settings dialog with tabs for Folders, AI, OpenCV, and Advanced options."""

import os
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QLabel, QLineEdit, QPushButton, QComboBox, QSpinBox,
    QDoubleSpinBox, QCheckBox, QGroupBox, QFormLayout,
    QFileDialog, QSlider, QMessageBox
)
from PySide6.QtCore import Qt


PROVIDER_MODELS = {
    "openrouter": [
        # Google Gemini (best cost/performance for vision)
        "google/gemini-2.5-flash-lite",
        "google/gemini-2.0-flash-001",
        "google/gemini-2.5-flash-preview-05-20",
        "google/gemini-2.5-pro-preview",
        "google/gemini-pro-vision",
        # Anthropic Claude (strong image understanding)
        "anthropic/claude-sonnet-4",
        "anthropic/claude-opus-4",
        "anthropic/claude-3.5-sonnet",
        "anthropic/claude-3-haiku",
        # OpenAI GPT (reliable vision)
        "openai/gpt-4o",
        "openai/gpt-4o-mini",
        "openai/gpt-4.1",
        "openai/gpt-4-vision-preview",
        # Meta Llama (open-source vision)
        "meta-llama/llama-3.2-90b-vision-instruct",
        "meta-llama/llama-3.2-11b-vision-instruct",
        # Mistral
        "mistralai/pixtral-large-2411",
        "mistralai/pixtral-12b",
        # Qwen (good multilingual + vision)
        "qwen/qwen-2-vl-72b-instruct",
        "qwen/qwen2.5-vl-72b-instruct",
    ],
    "openai": [
        "gpt-4o",
        "gpt-4o-mini",
        "gpt-4.1",
        "gpt-4.1-mini",
    ],
    "anthropic": [
        "claude-sonnet-4-20250514",
        "claude-haiku-4-5-20251001",
        "claude-opus-4-20250514",
    ],
}


class SettingsDialog(QDialog):
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self.setWindowTitle("Settings")
        self.setMinimumSize(550, 480)

        layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        self._build_folders_tab()
        self._build_ai_tab()
        self._build_opencv_tab()
        self._build_advanced_tab()

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        save_btn = QPushButton("Save")
        save_btn.setObjectName("primaryBtn")
        save_btn.clicked.connect(self._save)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)

    def _browse(self, line_edit):
        d = QFileDialog.getExistingDirectory(self, "Select Folder", line_edit.text())
        if d:
            line_edit.setText(d)

    def _build_folders_tab(self):
        tab = QWidget()
        form = QFormLayout(tab)
        form.setSpacing(12)

        self.output_folder = QLineEdit(self.config.get("folders", "output_folder", default=""))
        btn1 = QPushButton("Browse...")
        btn1.clicked.connect(lambda: self._browse(self.output_folder))
        row1 = QHBoxLayout()
        row1.addWidget(self.output_folder)
        row1.addWidget(btn1)
        form.addRow("Output Folder:", row1)

        self.reports_folder = QLineEdit(self.config.get("folders", "reports_folder", default=""))
        btn2 = QPushButton("Browse...")
        btn2.clicked.connect(lambda: self._browse(self.reports_folder))
        row2 = QHBoxLayout()
        row2.addWidget(self.reports_folder)
        row2.addWidget(btn2)
        form.addRow("Reports Folder:", row2)

        self.tabs.addTab(tab, "Folders")

    def _build_ai_tab(self):
        tab = QWidget()
        form = QFormLayout(tab)
        form.setSpacing(12)

        self.provider_combo = QComboBox()
        self.provider_combo.addItems(["openrouter", "openai", "anthropic"])
        self.provider_combo.setCurrentText(self.config.get("ai", "provider", default="openrouter"))
        self.provider_combo.currentTextChanged.connect(self._on_provider_changed)
        form.addRow("Provider:", self.provider_combo)

        self.api_key_edit = QLineEdit(self.config.get("ai", "api_key", default=""))
        self.api_key_edit.setEchoMode(QLineEdit.Password)
        show_btn = QPushButton("Show")
        show_btn.setFixedWidth(60)
        show_btn.clicked.connect(lambda: self.api_key_edit.setEchoMode(
            QLineEdit.Normal if self.api_key_edit.echoMode() == QLineEdit.Password else QLineEdit.Password
        ))
        key_row = QHBoxLayout()
        key_row.addWidget(self.api_key_edit)
        key_row.addWidget(show_btn)
        form.addRow("API Key:", key_row)

        self.model_combo = QComboBox()
        self.model_combo.setEditable(True)
        self._on_provider_changed(self.provider_combo.currentText())
        self.model_combo.setCurrentText(self.config.get("ai", "model_id", default="google/gemini-2.5-flash-lite"))
        form.addRow("Model:", self.model_combo)

        self.max_tokens_spin = QSpinBox()
        self.max_tokens_spin.setRange(100, 8192)
        self.max_tokens_spin.setValue(self.config.get("ai", "max_tokens", default=700))
        form.addRow("Max Tokens:", self.max_tokens_spin)

        self.detection_check = QCheckBox("Enable object detection (bounding boxes)")
        self.detection_check.setChecked(self.config.get("ai", "enable_object_detection", default=False))
        form.addRow("", self.detection_check)

        self.detection_mode = QComboBox()
        self.detection_mode.addItems(["precise", "quadrant"])
        self.detection_mode.setCurrentText(self.config.get("ai", "detection_mode", default="precise"))
        form.addRow("Detection Mode:", self.detection_mode)

        self.tabs.addTab(tab, "AI Config")

    def _on_provider_changed(self, provider):
        self.model_combo.clear()
        models = PROVIDER_MODELS.get(provider, [])
        self.model_combo.addItems(models)

    def _build_opencv_tab(self):
        tab = QWidget()
        form = QFormLayout(tab)
        form.setSpacing(10)

        cv = self.config.get_opencv_thresholds()

        self.motion_thresh = QSpinBox()
        self.motion_thresh.setRange(1, 255)
        self.motion_thresh.setValue(cv.get("motion_threshold", 25))
        form.addRow("Motion Threshold:", self.motion_thresh)

        self.motion_area = QSpinBox()
        self.motion_area.setRange(100, 10000)
        self.motion_area.setValue(cv.get("motion_min_area", 800))
        form.addRow("Motion Min Area (px):", self.motion_area)

        self.motion_contours = QSpinBox()
        self.motion_contours.setRange(1, 20)
        self.motion_contours.setValue(cv.get("motion_min_contours", 2))
        form.addRow("Motion Min Contours:", self.motion_contours)

        self.feature_kps = QSpinBox()
        self.feature_kps.setRange(10, 500)
        self.feature_kps.setValue(cv.get("feature_min_keypoints", 80))
        form.addRow("Feature Min Keypoints:", self.feature_kps)

        self.edge_density = QDoubleSpinBox()
        self.edge_density.setRange(0.001, 0.5)
        self.edge_density.setSingleStep(0.005)
        self.edge_density.setDecimals(3)
        self.edge_density.setValue(cv.get("edge_density_min", 0.04))
        form.addRow("Edge Density Min:", self.edge_density)

        self.dark_thresh = QSpinBox()
        self.dark_thresh.setRange(1, 100)
        self.dark_thresh.setValue(cv.get("dark_skip_threshold", 20))
        form.addRow("Dark Skip Threshold:", self.dark_thresh)

        self.turbid_thresh = QSpinBox()
        self.turbid_thresh.setRange(100, 255)
        self.turbid_thresh.setValue(cv.get("turbid_flag_threshold", 180))
        form.addRow("Turbidity Threshold:", self.turbid_thresh)

        self.colour_ratio = QDoubleSpinBox()
        self.colour_ratio.setRange(0.001, 0.2)
        self.colour_ratio.setSingleStep(0.005)
        self.colour_ratio.setDecimals(3)
        self.colour_ratio.setValue(cv.get("colour_anomaly_ratio", 0.02))
        form.addRow("Colour Anomaly Ratio:", self.colour_ratio)

        self.tabs.addTab(tab, "OpenCV")

    def _build_advanced_tab(self):
        tab = QWidget()
        form = QFormLayout(tab)
        form.setSpacing(12)

        self.frame_interval = QSpinBox()
        self.frame_interval.setRange(1, 30)
        self.frame_interval.setValue(self.config.get("extraction", "frame_every_sec", default=5))
        self.frame_interval.setSuffix(" sec")
        form.addRow("Frame Interval:", self.frame_interval)

        self.dedup_check = QCheckBox("Enable duplicate removal")
        self.dedup_check.setChecked(self.config.get("extraction", "dedup_enabled", default=True))
        form.addRow("", self.dedup_check)

        self.dedup_thresh = QDoubleSpinBox()
        self.dedup_thresh.setRange(0.3, 0.95)
        self.dedup_thresh.setSingleStep(0.05)
        self.dedup_thresh.setDecimals(2)
        self.dedup_thresh.setValue(self.config.get("extraction", "dedup_threshold", default=0.5))
        form.addRow("Dedup Threshold:", self.dedup_thresh)

        self.verify_check = QCheckBox("Verification mode (sample frames only)")
        self.verify_check.setChecked(self.config.get("ai", "verification_mode", default=False))
        form.addRow("", self.verify_check)

        self.verify_max = QSpinBox()
        self.verify_max.setRange(1, 100)
        self.verify_max.setValue(self.config.get("ai", "verification_max_frames", default=20))
        form.addRow("Max Verify Frames:", self.verify_max)

        self.tabs.addTab(tab, "Advanced")

    def _save(self):
        # Folders
        self.config.set("folders", "output_folder", self.output_folder.text())
        self.config.set("folders", "reports_folder", self.reports_folder.text())

        # AI
        self.config.set("ai", "provider", self.provider_combo.currentText())
        self.config.set("ai", "api_key", self.api_key_edit.text())
        self.config.set("ai", "model_id", self.model_combo.currentText())
        self.config.set("ai", "max_tokens", self.max_tokens_spin.value())
        self.config.set("ai", "enable_object_detection", self.detection_check.isChecked())
        self.config.set("ai", "detection_mode", self.detection_mode.currentText())

        # OpenCV
        self.config.set("opencv", "motion_threshold", self.motion_thresh.value())
        self.config.set("opencv", "motion_min_area", self.motion_area.value())
        self.config.set("opencv", "motion_min_contours", self.motion_contours.value())
        self.config.set("opencv", "feature_min_keypoints", self.feature_kps.value())
        self.config.set("opencv", "edge_density_min", self.edge_density.value())
        self.config.set("opencv", "dark_skip_threshold", self.dark_thresh.value())
        self.config.set("opencv", "turbid_flag_threshold", self.turbid_thresh.value())
        self.config.set("opencv", "colour_anomaly_ratio", self.colour_ratio.value())

        # Advanced
        self.config.set("extraction", "frame_every_sec", self.frame_interval.value())
        self.config.set("extraction", "dedup_enabled", self.dedup_check.isChecked())
        self.config.set("extraction", "dedup_threshold", self.dedup_thresh.value())
        self.config.set("ai", "verification_mode", self.verify_check.isChecked())
        self.config.set("ai", "verification_max_frames", self.verify_max.value())

        self.config.save()
        self.accept()
