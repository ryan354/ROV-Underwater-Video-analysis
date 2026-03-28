"""Scrollable thumbnail grid widget for displaying extracted frames."""

import os
from PySide6.QtWidgets import (
    QScrollArea, QWidget, QGridLayout, QLabel, QVBoxLayout, QSizePolicy
)
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtCore import Qt, Signal


class FrameCard(QWidget):
    """A single frame thumbnail card."""
    clicked = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.data = {}
        self.setFixedSize(140, 130)
        self.setCursor(Qt.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)

        self.thumb_label = QLabel()
        self.thumb_label.setFixedSize(132, 90)
        self.thumb_label.setAlignment(Qt.AlignCenter)
        self.thumb_label.setStyleSheet("border-radius: 4px;")
        self.thumb_label.setScaledContents(True)
        layout.addWidget(self.thumb_label)

        self.name_label = QLabel()
        self.name_label.setAlignment(Qt.AlignCenter)
        self.name_label.setStyleSheet("font-size: 10px; color: #a6adc8;")
        layout.addWidget(self.name_label)

        self.status_label = QLabel()
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("font-size: 9px; font-weight: bold;")
        layout.addWidget(self.status_label)

    def set_data(self, data):
        self.data = data
        frame_name = data.get("frame", "")
        self.name_label.setText(frame_name[:18])

        flagged = data.get("flagged", False)
        skipped = data.get("skipped", False)

        if skipped:
            self.setStyleSheet("FrameCard { border: 2px solid #585b70; border-radius: 6px; background-color: #181825; opacity: 0.5; }")
            self.status_label.setText("SKIP")
            self.status_label.setStyleSheet("font-size: 9px; font-weight: bold; color: #585b70;")
        elif flagged:
            urgency = data.get("analysis", {}).get("urgency", "")
            colors = {"high": "#f38ba8", "medium": "#fab387", "low": "#a6e3a1", "none": "#89b4fa"}
            color = colors.get(urgency, "#f9e2af")
            self.setStyleSheet(f"FrameCard {{ border: 2px solid {color}; border-radius: 6px; background-color: #181825; }}")
            self.status_label.setText("FLAG")
            self.status_label.setStyleSheet(f"font-size: 9px; font-weight: bold; color: {color};")
        else:
            self.setStyleSheet("FrameCard { border: 1px solid #313244; border-radius: 6px; background-color: #181825; }")
            self.status_label.setText("CLEAR")
            self.status_label.setStyleSheet("font-size: 9px; font-weight: bold; color: #45475a;")

        # Load thumbnail
        frame_path = data.get("frame_path", "")
        if frame_path and os.path.exists(frame_path):
            pixmap = QPixmap(frame_path)
            if not pixmap.isNull():
                self.thumb_label.setPixmap(
                    pixmap.scaled(132, 90, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                )
                return

        # Fallback: try the all_frames directory
        self.thumb_label.setText("No preview")
        self.thumb_label.setStyleSheet("border-radius: 4px; color: #585b70; background-color: #11111b;")

    def update_analysis(self, analysis):
        """Update the card with AI analysis results."""
        self.data["analysis"] = analysis
        urgency = analysis.get("urgency", "none")
        colors = {"high": "#f38ba8", "medium": "#fab387", "low": "#a6e3a1", "none": "#89b4fa"}
        color = colors.get(urgency, "#f9e2af")
        self.setStyleSheet(f"FrameCard {{ border: 2px solid {color}; border-radius: 6px; background-color: #181825; }}")
        self.status_label.setText(urgency.upper())
        self.status_label.setStyleSheet(f"font-size: 9px; font-weight: bold; color: {color};")

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.data)
        super().mousePressEvent(event)


class FrameGridWidget(QScrollArea):
    """Scrollable grid of frame thumbnails."""
    frame_clicked = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.container = QWidget()
        self.grid = QGridLayout(self.container)
        self.grid.setSpacing(6)
        self.grid.setContentsMargins(6, 6, 6, 6)
        self.setWidget(self.container)

        self.cards = []
        self.cols = 5

    def clear(self):
        """Remove all frame cards."""
        for card in self.cards:
            self.grid.removeWidget(card)
            card.deleteLater()
        self.cards = []

    def add_frame(self, data):
        """Add a frame card to the grid."""
        card = FrameCard()
        card.set_data(data)
        card.clicked.connect(self.frame_clicked.emit)

        idx = len(self.cards)
        row = idx // self.cols
        col = idx % self.cols
        self.grid.addWidget(card, row, col)
        self.cards.append(card)
        return card

    def update_frame_analysis(self, frame_name, analysis):
        """Update a specific frame card with analysis results."""
        for card in self.cards:
            if card.data.get("frame") == frame_name:
                card.update_analysis(analysis)
                break

    def resizeEvent(self, event):
        """Recalculate columns based on width."""
        width = self.viewport().width()
        new_cols = max(1, width // 148)
        if new_cols != self.cols and self.cards:
            self.cols = new_cols
            for i, card in enumerate(self.cards):
                self.grid.removeWidget(card)
                self.grid.addWidget(card, i // self.cols, i % self.cols)
        self.cols = new_cols
        super().resizeEvent(event)
