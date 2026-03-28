"""Frame annotation drawing for OpenCV flags and AI detections."""

import cv2
import shutil
import logging

log = logging.getLogger(__name__)


def draw_cv_annotations(frame_path, flags, out_path):
    """Draw OpenCV flag annotations on a frame."""
    img = cv2.imread(frame_path)
    if img is None:
        shutil.copy(frame_path, out_path)
        return
    cv2.rectangle(img, (0, 0), (img.shape[1] - 1, img.shape[0] - 1), (0, 0, 220), 5)
    y = 32
    for name, info in flags.items():
        cv2.putText(img, f"{name.upper()}: {info.get('reason', '')}", (10, y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2, cv2.LINE_AA)
        y += 30
    cv2.imwrite(out_path, img)


def draw_ai_detections(frame_path, detections, out_path, mode="precise"):
    """
    Draw AI-detected object annotations on a frame.

    Args:
        frame_path: Path to the original frame image
        detections: List of detection dicts from AI analysis
        out_path: Where to save the annotated frame
        mode: "precise" for bounding boxes, "quadrant" for region highlights
    """
    img = cv2.imread(frame_path)
    if img is None:
        shutil.copy(frame_path, out_path)
        return

    h, w = img.shape[:2]
    colors = [
        (0, 255, 0), (255, 0, 0), (0, 165, 255), (255, 255, 0),
        (255, 0, 255), (0, 255, 255), (128, 0, 255), (255, 128, 0),
    ]

    for i, det in enumerate(detections):
        color = colors[i % len(colors)]
        label = det.get("label", "object")
        conf = det.get("confidence", 0)
        text = f"{label} ({conf:.0%})" if conf else label

        if mode == "precise" and "bbox" in det:
            bbox = det["bbox"]
            # Normalized coordinates [x, y, w, h] in 0-1 range
            x1 = int(bbox[0] * w)
            y1 = int(bbox[1] * h)
            bw = int(bbox[2] * w)
            bh = int(bbox[3] * h)
            x2 = x1 + bw
            y2 = y1 + bh

            cv2.rectangle(img, (x1, y1), (x2, y2), color, 3)

            # Label background
            (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
            cv2.rectangle(img, (x1, y1 - th - 10), (x1 + tw + 6, y1), color, -1)
            cv2.putText(img, text, (x1 + 3, y1 - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2, cv2.LINE_AA)

        elif mode == "quadrant" and "region" in det:
            region = det["region"].lower().replace("-", " ").replace("_", " ")
            # Map region names to coordinates
            regions = {
                "top left": (0, 0, w // 2, h // 2),
                "top right": (w // 2, 0, w, h // 2),
                "bottom left": (0, h // 2, w // 2, h),
                "bottom right": (w // 2, h // 2, w, h),
                "center": (w // 4, h // 4, 3 * w // 4, 3 * h // 4),
                "top center": (w // 4, 0, 3 * w // 4, h // 2),
                "bottom center": (w // 4, h // 2, 3 * w // 4, h),
                "left center": (0, h // 4, w // 2, 3 * h // 4),
                "right center": (w // 2, h // 4, w, 3 * h // 4),
            }
            coords = regions.get(region, (0, 0, w, h))
            rx1, ry1, rx2, ry2 = coords

            # Semi-transparent overlay
            overlay = img.copy()
            cv2.rectangle(overlay, (rx1, ry1), (rx2, ry2), color, -1)
            cv2.addWeighted(overlay, 0.2, img, 0.8, 0, img)
            cv2.rectangle(img, (rx1, ry1), (rx2, ry2), color, 3)

            # Label
            label_y = ry1 + 25 if ry1 + 25 < h else ry2 - 10
            cv2.putText(img, text, (rx1 + 5, label_y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2, cv2.LINE_AA)

    # Draw legend in bottom-left
    if detections:
        legend_y = h - 20 - len(detections) * 22
        cv2.rectangle(img, (5, legend_y - 5), (250, h - 5), (0, 0, 0), -1)
        cv2.addWeighted(img, 0.7, cv2.imread(frame_path) if cv2.imread(frame_path) is not None else img, 0.3, 0, img)
        # Redraw legend area cleanly
        overlay = img.copy()
        cv2.rectangle(overlay, (5, legend_y - 5), (250, h - 5), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.6, img, 0.4, 0, img)
        for j, det in enumerate(detections):
            color = colors[j % len(colors)]
            ly = legend_y + j * 22 + 15
            cv2.rectangle(img, (10, ly - 12), (24, ly + 2), color, -1)
            label = det.get("label", "object")
            conf = det.get("confidence", 0)
            txt = f"{label} ({conf:.0%})" if conf else label
            cv2.putText(img, txt, (30, ly),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)

    cv2.imwrite(out_path, img)
