"""Configuration management for the ROV Analyzer application."""

import os
import json
import logging
from pathlib import Path

from rov_app.core.constants import (
    DEFAULT_OPENCV_THRESHOLDS, DEFAULT_FRAME_EVERY_SEC,
    DEFAULT_MAX_TOKENS, DEFAULT_VERIFICATION_MAX_FRAMES,
    DEFAULT_DEDUP_THRESHOLD, SUPPORTED_EXTS,
)

log = logging.getLogger(__name__)

DEFAULT_CONFIG = {
    "folders": {
        "output_folder": "",
        "reports_folder": "",
    },
    "ai": {
        "provider": "openrouter",
        "api_key": "",
        "model_id": "google/gemini-2.5-flash-lite",
        "max_tokens": DEFAULT_MAX_TOKENS,
        "verification_mode": False,
        "verification_max_frames": DEFAULT_VERIFICATION_MAX_FRAMES,
        "detection_mode": "precise",  # "precise" or "quadrant"
        "enable_object_detection": False,
    },
    "opencv": DEFAULT_OPENCV_THRESHOLDS.copy(),
    "extraction": {
        "frame_every_sec": DEFAULT_FRAME_EVERY_SEC,
        "supported_exts": SUPPORTED_EXTS[:],
        "dedup_enabled": True,
        "dedup_threshold": DEFAULT_DEDUP_THRESHOLD,
    },
    "report": {
        "languages": ["en"],
    },
}


class ConfigManager:
    """Manages application configuration with JSON persistence."""

    def __init__(self, config_path=None):
        # Default to config.json next to the app
        if config_path is None:
            app_dir = Path(__file__).parent.parent.parent
            config_path = str(app_dir / "config.json")
        self.config_path = config_path
        self._data = {}
        self.load()

    def load(self):
        """Load config from file, falling back to defaults."""
        self._data = json.loads(json.dumps(DEFAULT_CONFIG))  # deep copy

        # Load user config if exists
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    user_data = json.load(f)
                self._deep_merge(self._data, user_data)
                log.info(f"Config loaded: {self.config_path}")
            except Exception as e:
                log.warning(f"Config load error: {e}")

        # Fallback: try .env file
        try:
            from dotenv import load_dotenv
            env_path = Path(self.config_path).parent / ".env"
            if env_path.exists():
                load_dotenv(env_path)
                self._apply_env_overrides()
        except ImportError:
            pass

    def _apply_env_overrides(self):
        """Override config values from environment variables."""
        env_map = {
            "OPENROUTER_API_KEY": ("ai", "api_key"),
            "MODEL_ID": ("ai", "model_id"),
            "OUTPUT_FOLDER": ("folders", "output_folder"),
            "REPORTS_FOLDER": ("folders", "reports_folder"),
            "FRAME_EVERY_SEC": ("extraction", "frame_every_sec"),
        }
        for env_key, (section, key) in env_map.items():
            val = os.environ.get(env_key)
            if val:
                if key == "frame_every_sec":
                    val = int(val)
                self._data[section][key] = val

    def _deep_merge(self, base, override):
        """Merge override dict into base dict recursively."""
        for key, val in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(val, dict):
                self._deep_merge(base[key], val)
            else:
                base[key] = val

    def save(self):
        """Save current config to file."""
        os.makedirs(os.path.dirname(self.config_path) or ".", exist_ok=True)
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2, ensure_ascii=False)
        log.info(f"Config saved: {self.config_path}")

    def get(self, *keys, default=None):
        """Get a nested config value. Usage: config.get("ai", "provider")"""
        d = self._data
        for k in keys:
            if isinstance(d, dict) and k in d:
                d = d[k]
            else:
                return default
        return d

    def set(self, *keys_and_value):
        """Set a nested config value. Usage: config.set("ai", "provider", "openai")"""
        *keys, value = keys_and_value
        d = self._data
        for k in keys[:-1]:
            if k not in d:
                d[k] = {}
            d = d[k]
        d[keys[-1]] = value

    @property
    def data(self):
        return self._data

    def get_opencv_thresholds(self):
        """Get OpenCV thresholds dict."""
        return self._data.get("opencv", DEFAULT_OPENCV_THRESHOLDS.copy())
