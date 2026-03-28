"""Default constants and thresholds for ROV analysis."""

# Supported video formats
SUPPORTED_EXTS = [".mp4", ".avi", ".mkv", ".mov"]

# Minimum file size to process (MB)
MIN_FILE_SIZE_MB = 1

# Frame extraction
DEFAULT_FRAME_EVERY_SEC = 5

# OpenCV thresholds
DEFAULT_OPENCV_THRESHOLDS = {
    "motion_threshold": 25,
    "motion_min_area": 800,
    "motion_min_contours": 2,
    "feature_min_keypoints": 80,
    "edge_density_min": 0.04,
    "dark_skip_threshold": 20,
    "turbid_flag_threshold": 180,
    "colour_anomaly_ratio": 0.02,
}

# Deduplication
DEFAULT_DEDUP_THRESHOLD = 0.5  # Dedup sensitivity: lower=aggressive (removes more), higher=permissive (keeps more)

# AI analysis
DEFAULT_MAX_TOKENS = 700
DEFAULT_VERIFICATION_MAX_FRAMES = 20

# PDF urgency colors (RGB)
URGENCY_RGB = {
    "high":   (180, 0,   0),
    "medium": (190, 95,  0),
    "low":    (0,   110, 50),
    "none":   (70,  70,  70),
}
