"""
Bone Segmentation — classical OpenCV approach (no separate deep model needed).

Bones show up as the brightest, highest-contrast regions in an X-ray, so
within the YOLO-detected bounding box we can reliably isolate the bone
using adaptive thresholding + contour detection, without needing a
pixel-level annotated dataset (which doesn't cleanly exist for this task).

Pipeline (within the ROI only):
    Crop to YOLO bbox
        -> Grayscale + CLAHE (contrast enhancement)
        -> Gaussian blur (denoise)
        -> Otsu thresholding (bone = bright = foreground)
        -> ALL significant contours = the bone piece(s)
        -> Binary mask

NOTE: we intentionally keep ALL significant contours, not just the largest.
A fractured bone often appears as 2+ separate pieces (above/below the
fracture line) — discarding smaller pieces would throw away exactly the
information needed to measure the fracture gap (see measurements.py).
"""

from dataclasses import dataclass
from typing import Tuple

import cv2
import numpy as np

from app.ai_structural.preprocessing import auto_enhance_xray


@dataclass
class SegmentationResult:
    mask: np.ndarray            # binary mask, same size as the cropped ROI
    contour: np.ndarray         # the single largest contour (for simple use cases)
    roi_offset: Tuple[int, int]  # (x1, y1) offset of ROI within original image


def preprocess_xray(image: np.ndarray) -> np.ndarray:
    """
    Standard X-ray cleanup before segmentation. Delegates to the shared
    auto_enhance_xray (brightness normalization + CLAHE + denoising) so
    detection and segmentation see consistently-processed images.
    """
    return auto_enhance_xray(image)


def segment_bone(image: np.ndarray, bbox: Tuple[int, int, int, int]) -> SegmentationResult:
    """
    image: full original X-ray (as loaded by cv2.imread)
    bbox: (x1, y1, x2, y2) from YOLO detection
    """
    x1, y1, x2, y2 = bbox
    roi = image[y1:y2, x1:x2]

    if roi.size == 0:
        raise ValueError("Empty region of interest — check YOLO bbox coordinates.")

    processed = preprocess_xray(roi)

    # Otsu's method auto-picks the best threshold to separate bone (bright)
    # from soft tissue/background (darker) — no manual tuning needed.
    _, binary = cv2.threshold(processed, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # Clean up small noise specks / fill small holes
    kernel = np.ones((5, 5), np.uint8)
    cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
    cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_OPEN, kernel)

    contours, _ = cv2.findContours(cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        raise ValueError("No bone contour found after segmentation — check image quality.")

    # Keep ALL significant contours (>= 3% of the largest contour's area),
    # not just the single largest — see module docstring for why.
    areas = [cv2.contourArea(c) for c in contours]
    max_area = max(areas)
    significant_contours = [
        c for c, a in zip(contours, areas) if a >= max_area * 0.03
    ]

    mask = np.zeros_like(cleaned)
    cv2.drawContours(mask, significant_contours, -1, 255, thickness=cv2.FILLED)

    largest_contour = max(contours, key=cv2.contourArea)

    return SegmentationResult(
        mask=mask,
        contour=largest_contour,
        roi_offset=(x1, y1),
    )
