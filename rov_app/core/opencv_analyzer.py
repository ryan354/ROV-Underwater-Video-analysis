"""OpenCV-based frame analysis for underwater ROV footage."""

import cv2
import numpy as np
import logging

from rov_app.core.constants import DEFAULT_OPENCV_THRESHOLDS

log = logging.getLogger(__name__)


class OpenCVAnalyzer:
    """Analyzes frames for motion, features, edges, turbidity, and color anomalies."""

    def __init__(self, thresholds=None):
        self.prev_gray = None
        self.orb = cv2.ORB_create(nfeatures=500)
        self.t = {**DEFAULT_OPENCV_THRESHOLDS, **(thresholds or {})}

    def reset(self):
        """Reset state for a new video."""
        self.prev_gray = None

    def analyze(self, frame_path):
        """
        Analyze a single frame and return flags dict.
        Returns dict with detected flags, or {"skip": reason} / {"error": reason}.
        """
        img = cv2.imread(frame_path)
        if img is None:
            self.prev_gray = None
            return {"error": "unreadable"}

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        brightness = float(np.mean(gray))

        if brightness < self.t["dark_skip_threshold"]:
            return {"skip": f"too dark ({brightness:.1f})"}

        flags = {}

        # Motion detection
        if self.prev_gray is not None:
            diff = cv2.absdiff(self.prev_gray, gray)
            _, thresh = cv2.threshold(diff, self.t["motion_threshold"], 255, cv2.THRESH_BINARY)
            k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
            thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, k)
            thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, k)
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            big = [c for c in contours if cv2.contourArea(c) > self.t["motion_min_area"]]
            if len(big) >= self.t["motion_min_contours"]:
                flags["motion"] = {
                    "contour_count": len(big),
                    "total_area_px": int(sum(cv2.contourArea(c) for c in big)),
                    "reason": "Moving object or ROV movement detected"
                }

        # Feature detection (ORB)
        kps, _ = self.orb.detectAndCompute(gray, None)
        if len(kps) >= self.t["feature_min_keypoints"]:
            flags["features"] = {
                "keypoint_count": len(kps),
                "reason": "Rich texture or structure detected"
            }

        # Edge detection
        edges = cv2.Canny(gray, 50, 150)
        edge_density = float(np.count_nonzero(edges)) / (gray.shape[0] * gray.shape[1])
        if edge_density >= self.t["edge_density_min"]:
            flags["edges"] = {
                "density": round(edge_density, 4),
                "reason": "High edge density - possible structure"
            }

        # Turbidity check
        if brightness > self.t["turbid_flag_threshold"]:
            flags["turbidity"] = {
                "brightness": round(brightness, 1),
                "reason": "High brightness - turbidity or light"
            }

        # Color anomaly detection
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        red1 = cv2.inRange(hsv, (0, 50, 50), (10, 255, 255))
        red2 = cv2.inRange(hsv, (160, 50, 50), (180, 255, 255))
        orange = cv2.inRange(hsv, (10, 50, 50), (30, 255, 255))
        ratio = (cv2.countNonZero(red1) + cv2.countNonZero(red2) +
                 cv2.countNonZero(orange)) / (img.shape[0] * img.shape[1])
        if ratio > self.t["colour_anomaly_ratio"]:
            flags["colour"] = {
                "unusual_ratio": round(ratio, 4),
                "reason": "Unusual colour - marine life, rust, or debris"
            }

        self.prev_gray = gray
        return flags
