"""Duplicate frame removal using ORB feature matching + histogram comparison."""

import cv2
import numpy as np
import logging

log = logging.getLogger(__name__)


class FrameDeduplicator:
    """Remove near-duplicate frames using ORB features and color histograms.

    The similarity_threshold controls how aggressively duplicates are removed.
    Lower = more aggressive (removes more frames), higher = more permissive.
    Recommended range: 0.4 (aggressive) to 0.9 (permissive).
    """

    def __init__(self, similarity_threshold=0.5, window_size=10):
        """
        Args:
            similarity_threshold: Overall duplicate sensitivity (0.0-1.0).
                Lower values = more aggressive dedup, removes more similar frames.
                Higher values = more permissive, keeps more frames.
                Maps to both histogram and ORB thresholds internally.
            window_size: Compare each frame against this many recent unique frames.
        """
        self.similarity_threshold = similarity_threshold
        # Map the single threshold to histogram and ORB thresholds:
        # - Histogram: at threshold=0.5, hist_thresh=0.85; at 0.9, hist_thresh=0.97
        # - ORB: directly used as the ORB match ratio threshold
        self.histogram_threshold = 0.75 + (similarity_threshold * 0.22)
        self.orb_threshold = similarity_threshold * 0.6
        self.window_size = window_size
        self.orb = cv2.ORB_create(nfeatures=500)
        self.bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)

        log.info(f"Dedup init: threshold={similarity_threshold:.2f} "
                 f"-> hist_thresh={self.histogram_threshold:.3f}, "
                 f"orb_thresh={self.orb_threshold:.3f}, window={window_size}")

    def _compute_histogram(self, img_path):
        """Compute normalized HSV histogram for an image."""
        img = cv2.imread(img_path)
        if img is None:
            return None
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        hist = cv2.calcHist([hsv], [0, 1], None, [32, 32], [0, 180, 0, 256])
        cv2.normalize(hist, hist)
        return hist

    def _compute_structural_hash(self, img_path, hash_size=16):
        """Compute a perceptual hash (dHash) for fast structural comparison."""
        img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            return None
        resized = cv2.resize(img, (hash_size + 1, hash_size))
        # Difference hash: compare adjacent pixels
        diff = resized[:, 1:] > resized[:, :-1]
        return diff.flatten()

    def compute_similarity(self, path_a, path_b):
        """Compute ORB feature similarity between two frames. Returns 0.0-1.0."""
        img_a = cv2.imread(path_a, cv2.IMREAD_GRAYSCALE)
        img_b = cv2.imread(path_b, cv2.IMREAD_GRAYSCALE)
        if img_a is None or img_b is None:
            return 0.0

        kps_a, des_a = self.orb.detectAndCompute(img_a, None)
        kps_b, des_b = self.orb.detectAndCompute(img_b, None)

        if des_a is None or des_b is None or len(kps_a) < 10 or len(kps_b) < 10:
            return 0.0

        matches = self.bf.knnMatch(des_a, des_b, k=2)
        good = []
        for pair in matches:
            if len(pair) == 2:
                m, n = pair
                if m.distance < 0.75 * n.distance:
                    good.append(m)

        max_kps = max(len(kps_a), len(kps_b))
        return len(good) / max_kps if max_kps > 0 else 0.0

    def compute_histogram_similarity(self, hist_a, hist_b):
        """Compute histogram correlation between two frames. Returns -1.0 to 1.0."""
        if hist_a is None or hist_b is None:
            return 0.0
        return cv2.compareHist(hist_a, hist_b, cv2.HISTCMP_CORREL)

    def compute_hash_similarity(self, hash_a, hash_b):
        """Compute perceptual hash similarity. Returns 0.0-1.0."""
        if hash_a is None or hash_b is None:
            return 0.0
        return np.count_nonzero(hash_a == hash_b) / len(hash_a)

    def is_duplicate(self, current_path, current_hist, current_hash,
                     recent_unique_paths, recent_unique_hists, recent_unique_hashes):
        """Check if current frame is a duplicate of any recent unique frame.

        Uses 3-layer comparison:
        1. Perceptual hash (fast, catches near-identical frames)
        2. Histogram correlation (fast, catches same-scene frames)
        3. ORB features (slower, catches structurally similar frames)

        A frame is duplicate if ANY layer says it's a match.
        """
        for prev_path, prev_hist, prev_hash in zip(
                recent_unique_paths, recent_unique_hists, recent_unique_hashes):

            # Layer 1: Perceptual hash (very fast)
            hash_sim = self.compute_hash_similarity(current_hash, prev_hash)
            if hash_sim >= 0.90:  # >90% identical pixels = definitely duplicate
                log.debug(f"Hash duplicate (sim={hash_sim:.3f})")
                return True

            # Layer 2: Histogram similarity
            hist_sim = self.compute_histogram_similarity(current_hist, prev_hist)
            if hist_sim >= self.histogram_threshold:
                log.debug(f"Histogram duplicate (corr={hist_sim:.3f}, thresh={self.histogram_threshold:.3f})")
                return True

            # Layer 3: ORB features (only if histogram shows moderate similarity)
            if hist_sim >= 0.6:
                orb_sim = self.compute_similarity(prev_path, current_path)
                if orb_sim >= self.orb_threshold:
                    log.debug(f"ORB duplicate (sim={orb_sim:.3f}, hist={hist_sim:.3f})")
                    return True

        return False

    def deduplicate(self, frame_items, on_progress=None):
        """
        Remove duplicate frames from a list of flagged items.

        Args:
            frame_items: List of dicts with 'frame_path' key.
            on_progress: Optional callback(current, total)

        Returns:
            (unique_items, duplicate_count)
        """
        if len(frame_items) <= 1:
            return frame_items, 0

        total = len(frame_items)

        # Pre-compute histograms and hashes for all frames
        histograms = []
        hashes = []
        for item in frame_items:
            path = item.get("frame_path", "")
            if path:
                histograms.append(self._compute_histogram(path))
                hashes.append(self._compute_structural_hash(path))
            else:
                histograms.append(None)
                hashes.append(None)

        unique = [frame_items[0]]
        unique_paths = [frame_items[0].get("frame_path", "")]
        unique_hists = [histograms[0]]
        unique_hashes = [hashes[0]]
        dup_count = 0

        for i in range(1, total):
            current_path = frame_items[i].get("frame_path", "")

            if on_progress:
                on_progress(i, total)

            if not current_path:
                unique.append(frame_items[i])
                unique_paths.append(current_path)
                unique_hists.append(histograms[i])
                unique_hashes.append(hashes[i])
                continue

            # Compare against recent unique frames (sliding window)
            window_paths = unique_paths[-self.window_size:]
            window_hists = unique_hists[-self.window_size:]
            window_hashes = unique_hashes[-self.window_size:]

            if self.is_duplicate(current_path, histograms[i], hashes[i],
                                 window_paths, window_hists, window_hashes):
                dup_count += 1
                log.debug(f"Duplicate: {frame_items[i].get('frame', '?')}")
            else:
                unique.append(frame_items[i])
                unique_paths.append(current_path)
                unique_hists.append(histograms[i])
                unique_hashes.append(hashes[i])

        if on_progress:
            on_progress(total, total)

        log.info(f"Dedup: {total} -> {len(unique)} unique ({dup_count} duplicates removed)")
        return unique, dup_count
