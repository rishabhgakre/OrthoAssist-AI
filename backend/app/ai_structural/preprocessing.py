"""
Image preprocessing shared by both detection and segmentation.

Real-world X-ray images uploaded via phone camera (photographing a physical
film or a screen) are often dark, low-contrast, or unevenly lit — very
different from the clean, pre-digitized X-rays in FracAtlas. This module
automatically normalizes brightness/contrast BEFORE the image reaches YOLO
or the segmentation step, so both stages see a more consistent, well-lit
image regardless of how the photo was originally taken.
"""

import cv2
import numpy as np


def _estimate_brightness(gray: np.ndarray) -> float:
    """Mean pixel intensity, 0 (black) to 255 (white)."""
    return float(np.mean(gray))


def _gamma_correct(gray: np.ndarray, gamma: float) -> np.ndarray:
    """
    Applies gamma correction: output = 255 * (input/255)^(1/gamma).
    gamma > 1 brightens (lifts shadows), gamma < 1 darkens (recovers highlights).
    Non-linear, so it preserves more detail than a flat brightness addition would.
    """
    inv_gamma = 1.0 / gamma
    table = np.array(
        [((i / 255.0) ** inv_gamma) * 255 for i in range(256)]
    ).astype("uint8")
    return cv2.LUT(gray, table)


def auto_enhance_xray(image: np.ndarray) -> np.ndarray:
    """
    Normalizes an X-ray image (or phone photo of one) for consistent
    downstream detection/segmentation:
        1. Convert to grayscale
        2. Auto-brighten if the image is dark (common with phone photos of
           a film/lightbox, or a dim screen photo)
        3. CLAHE local contrast enhancement (brings out bone edges even in
           unevenly-lit regions of the same image)
        4. Light denoising (phone camera sensor noise, compression artifacts)

    Returns a single-channel (grayscale) image ready for detection/segmentation.
    """
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()

    brightness = _estimate_brightness(gray)

    # Target a mid-range brightness (~130/255). Real X-rays and clean scans
    # are usually already in a reasonable range; dark phone photos often sit
    # well below 80 — those get a real gamma boost. Bright/glare-heavy phone
    # photos (screen photos with reflections) get mildly darkened instead.
    if brightness < 60:
        gray = _gamma_correct(gray, gamma=2.5)   # strong brighten
    elif brightness < 100:
        gray = _gamma_correct(gray, gamma=1.6)   # moderate brighten
    elif brightness > 200:
        gray = _gamma_correct(gray, gamma=0.7)   # mild darken (glare/overexposure)

    # CLAHE: enhances local contrast so bone edges are visible even if
    # lighting was uneven across the photo (common with phone shots of a
    # film held up to a light source, or angled screen photos)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)

    # Light denoising — phone camera sensor noise / JPEG compression
    # artifacts are much more common than in clean digital X-ray exports
    denoised = cv2.fastNlMeansDenoising(enhanced, h=7, templateWindowSize=7, searchWindowSize=21)

    return denoised


def enhance_for_detection(image: np.ndarray) -> np.ndarray:
    """
    Returns a 3-channel (BGR) version of the enhanced image, since YOLO
    expects color input even though our enhancement is grayscale-based.
    """
    enhanced_gray = auto_enhance_xray(image)
    return cv2.cvtColor(enhanced_gray, cv2.COLOR_GRAY2BGR)
