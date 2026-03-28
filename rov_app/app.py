"""Application entry point — creates QApplication and launches MainWindow."""

import sys
import logging
from pathlib import Path

from PySide6.QtWidgets import QApplication

from rov_app.core.config import ConfigManager
from rov_app.ui.main_window import MainWindow
from rov_app.ui.styles import DARK_STYLE

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler("rov_app.log", encoding="utf-8"),
        logging.StreamHandler(),
    ]
)


def run():
    app = QApplication(sys.argv)
    app.setApplicationName("ROV Underwater Analyzer")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("ROV Analyzer")
    app.setStyleSheet(DARK_STYLE)

    config = ConfigManager()
    window = MainWindow(config)
    window.show()

    return app.exec()
