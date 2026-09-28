"""
OpenCV Measurements — extracts clinically-relevant numbers from a bone mask.

For a fractured bone, the contour is often split into two separate pieces
(above and below the fracture line) — we detect this and measure the gap
between them. For a healed/aligned bone, the contour is closer to one
continuous piece.
"""

import math
from dataclasses import dataclass

import cv2
import numpy as np

from app.ai_structural.segmentation import SegmentationResult


@dataclass
class BoneMeasurements:
    gap_mm: float                # estimated fracture gap (0 if continuous)
    alignment_pct: float         # 0-100, how straight the bone axis is
    continuity_pct: float        # 0-100, how unbroken the bone contour is
    bone_angle_deg: float        # measured long-axis angle of the bone


def _fit_bone_axis_angle(mask: np.ndarray) -> float:
    """
    Fits a line through the bone mask's principal axis using PCA on the
    white pixel coordinates, and returns the angle (degrees) from vertical.
    """
    ys, xs = np.where(mask > 0)
    if len(xs) < 2:
        return 0.0

    points = np.column_stack((xs, ys)).astype(np.float64)
    mean = points.mean(axis=0)
    centered = points - mean

    cov = np.cov(centered.T)
    eigvals, eigvecs = np.linalg.eigh(cov)
    principal_axis = eigvecs[:, np.argmax(eigvals)]  # direction of most variance = bone's long axis

    angle_rad = math.atan2(principal_axis[1], principal_axis[0])
    angle_deg = math.degrees(angle_rad) % 180
    return angle_deg


def _find_contour_pieces(mask: np.ndarray, min_area_ratio: float = 0.03):
    """
    Finds separate significant contour pieces in the mask. A fractured bone
    often shows as 2+ disconnected blobs; a well-healed bone as 1.
    Small noise contours (below min_area_ratio of the largest) are ignored.
    """
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return []

    areas = [cv2.contourArea(c) for c in contours]
    max_area = max(areas)
    significant = [c for c, a in zip(contours, areas) if a >= max_area * min_area_ratio]
    # Sort top-to-bottom (by topmost y-coordinate) so piece order is consistent
    significant.sort(key=lambda c: c[:, 0, 1].min())
    return significant


def _estimate_gap_mm(pieces, pixel_to_mm: float) -> float:
    """
    If the bone mask is split into 2+ pieces, estimates the gap between the
    two closest edges of the top and bottom pieces (the fracture line).
    Returns 0.0 if the bone is a single continuous piece (no visible gap).
    """
    if len(pieces) < 2:
        return 0.0

    top_piece, bottom_piece = pieces[0], pieces[1]

    # Closest-point distance between the two contours (brute-force, contours are small)
    min_dist = float("inf")
    top_pts = top_piece.reshape(-1, 2)
    bottom_pts = bottom_piece.reshape(-1, 2)

    # Subsample for speed if contours are large
    top_sample = top_pts[::max(1, len(top_pts) // 100)]
    bottom_sample = bottom_pts[::max(1, len(bottom_pts) // 100)]

    for p1 in top_sample:
        dists = np.linalg.norm(bottom_sample - p1, axis=1)
        min_dist = min(min_dist, dists.min())

    return round(min_dist * pixel_to_mm, 2)


def _estimate_continuity_pct(pieces, mask: np.ndarray) -> float:
    """
    Continuity = how much of the bone's bounding region is filled by bone
    mask vs gaps. A single continuous piece scores near 100%; a bone split
    by a large visible fracture gap scores lower.
    """
    if len(pieces) <= 1:
        return 100.0

    total_piece_area = sum(cv2.contourArea(c) for c in pieces)
    bounding_area = mask.shape[0] * mask.shape[1]

    fill_ratio = total_piece_area / bounding_area if bounding_area > 0 else 0
    # Normalize against a reasonable "healthy" fill ratio ceiling (~0.5 of ROI)
    continuity = min(100.0, (fill_ratio / 0.5) * 100.0)
    return round(continuity, 1)


def measure_bone(
    segmentation: SegmentationResult,
    pixel_to_mm: float = 0.2,
) -> BoneMeasurements:
    """
    pixel_to_mm: calibration factor. X-rays don't have a fixed real-world
    scale without a calibration marker in the image, so this is a
    configurable estimate — document this assumption clearly in your report,
    or improve it by detecting a known-size reference object if available.
    """
    mask = segmentation.mask
    pieces = _find_contour_pieces(mask)

    angle = _fit_bone_axis_angle(mask)
    gap = _estimate_gap_mm(pieces, pixel_to_mm)
    continuity = _estimate_continuity_pct(pieces, mask)

    # Alignment: how close the bone axis is to vertical (0/180deg = perfectly
    # vertical in a typical AP X-ray framing). This is a simplifying
    # assumption — works for limb X-rays framed the standard way.
    deviation_from_vertical = min(abs(angle - 90), abs(angle - 0), abs(angle - 180))
    alignment_pct = max(0.0, 100.0 - (deviation_from_vertical / 45.0) * 100.0)

    return BoneMeasurements(
        gap_mm=gap,
        alignment_pct=round(alignment_pct, 1),
        continuity_pct=continuity,
        bone_angle_deg=round(angle, 1),
    )
