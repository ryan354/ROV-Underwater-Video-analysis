"""Dialog for viewing full-size frame with analysis details."""

import os
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
    QWidget, QGroupBox, QFormLayout
)
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt

from rov_app.core.telemetry import fmt_telemetry, fmt_flags


class FrameDetailDialog(QDialog):
    def __init__(self, data, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Frame Detail - {data.get('frame', '')}")
        self.setMinimumSize(900, 650)

        layout = QHBoxLayout(self)

        # Left: frame image
        img_scroll = QScrollArea()
        img_scroll.setWidgetResizable(True)
        img_label = QLabel()
        img_label.setAlignment(Qt.AlignCenter)

        frame_path = data.get("detected_frame_path") or data.get("frame_path", "")
        if frame_path and os.path.exists(frame_path):
            pixmap = QPixmap(frame_path)
            img_label.setPixmap(pixmap.scaled(600, 500, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            img_label.setText("No image available")
            img_label.setStyleSheet("color: #585b70; font-size: 16px;")

        img_scroll.setWidget(img_label)
        layout.addWidget(img_scroll, stretch=2)

        # Right: details panel
        detail_panel = QScrollArea()
        detail_panel.setWidgetResizable(True)
        detail_widget = QWidget()
        detail_layout = QVBoxLayout(detail_widget)

        # Frame info
        info_group = QGroupBox("Frame Info")
        info_form = QFormLayout(info_group)
        info_form.addRow("Frame:", QLabel(data.get("frame", "N/A")))
        info_form.addRow("Timestamp:", QLabel(data.get("timestamp", data.get("telemetry", {}).get("timestamp", "N/A"))))
        info_form.addRow("Flagged:", QLabel("Yes" if data.get("flagged") else "No"))
        detail_layout.addWidget(info_group)

        # Telemetry
        telem = data.get("telemetry", {})
        if telem:
            telem_group = QGroupBox("Telemetry")
            telem_form = QFormLayout(telem_group)
            for key in ["depth", "altitude", "heading", "speed", "pitch", "roll", "temp"]:
                if key in telem:
                    telem_form.addRow(f"{key.capitalize()}:", QLabel(str(telem[key])))
            if telem_form.rowCount() == 0:
                telem_form.addRow("Raw:", QLabel(str(telem.get("raw", "N/A"))[:100]))
            detail_layout.addWidget(telem_group)

        # CV Flags
        cv_flags = data.get("cv_flags", {})
        if cv_flags and not any(k in cv_flags for k in ("skip", "error")):
            cv_group = QGroupBox("OpenCV Signals")
            cv_form = QFormLayout(cv_group)
            for name, info in cv_flags.items():
                cv_form.addRow(f"{name.upper()}:", QLabel(info.get("reason", str(info))))
            detail_layout.addWidget(cv_group)

        # AI Analysis
        analysis = data.get("analysis", {})
        if analysis:
            ai_group = QGroupBox("AI Analysis")
            ai_form = QFormLayout(ai_group)

            urgency = analysis.get("urgency", "none")
            colors = {"high": "#f38ba8", "medium": "#fab387", "low": "#a6e3a1", "none": "#a6adc8"}
            urgency_label = QLabel(urgency.upper())
            urgency_label.setStyleSheet(f"color: {colors.get(urgency, '#cdd6f4')}; font-weight: bold;")
            ai_form.addRow("Urgency:", urgency_label)
            ai_form.addRow("Confidence:", QLabel(f"{analysis.get('confidence', 0):.0%}"))

            if analysis.get("one_line_summary"):
                summary_label = QLabel(analysis["one_line_summary"])
                summary_label.setWordWrap(True)
                ai_form.addRow("Summary:", summary_label)

            obj = analysis.get("objects", {})
            if obj.get("detected"):
                items = [str(o) for o in obj.get("list", []) if not isinstance(o, dict)]
                ai_form.addRow("Objects:", QLabel(", ".join(items)))
                if obj.get("details"):
                    d_label = QLabel(str(obj["details"]))
                    d_label.setWordWrap(True)
                    ai_form.addRow("Details:", d_label)

            struc = analysis.get("structures", {})
            if struc.get("detected"):
                items = [str(s) for s in struc.get("list", []) if not isinstance(s, dict)]
                ai_form.addRow("Structures:", QLabel(", ".join(items)))

            ano = analysis.get("anomalies", {})
            if ano.get("detected"):
                ai_form.addRow("Anomalies:", QLabel(str(ano.get("description", ""))))

            sb = analysis.get("seabed", {})
            if sb:
                ai_form.addRow("Seabed:", QLabel(str(sb.get("type", "N/A"))))

            ai_form.addRow("Visibility:", QLabel(str(analysis.get("visibility", "N/A"))))
            ai_form.addRow("Water Clarity:", QLabel(str(analysis.get("water_clarity", "N/A"))))

            if analysis.get("urgency_reason"):
                reason_label = QLabel(analysis["urgency_reason"])
                reason_label.setWordWrap(True)
                ai_form.addRow("Reason:", reason_label)

            detail_layout.addWidget(ai_group)

        detail_layout.addStretch()
        detail_panel.setWidget(detail_widget)
        layout.addWidget(detail_panel, stretch=1)
