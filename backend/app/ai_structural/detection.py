"""
YOLO Bone Detection wrapper.

Loads the model fine-tuned on FracAtlas (see ai_training/train_fracture_yolo.ipynb)
and returns the detected bone/fracture region as a bounding box.

If no trained weights exist yet (best.pt not placed in weights/), this raises
a clear error rather than silently failing or falling back to a useless
untrained model — you need to run the training notebook first.
"""

import os
from dataclasses import dataclass
from typing import Optional, Tuple

import cv2
import numpy as np
from ultralytics import YOLO

from app.core.config import settings
from app.ai_structural.preprocessing import enhance_for_detection

_model_cache: Optional[YOLO] = None


@dataclass
class Detection:
    bbox: Tuple[int, int, int, int]   # x1, y1, x2, y2 in pixel coords
    confidence: float
    class_name: str


def _get_model() -> YOLO:
    """Loads the trained YOLO model once and reuses it (avoids reloading per-request)."""
    global _model_cache
    if _model_cache is None:
        weights_path = settings.YOLO_WEIGHTS_PATH
        if not os.path.exists(weights_path):
            raise FileNotFoundError(
                f"YOLO weights not found at '{weights_path}'. "
                f"Run ai_training/train_fracture_yolo.ipynb in Google Colab first, "
                f"then place the downloaded best.pt at this path."
            )
        _model_cache = YOLO(weights_path)
    return _model_cache


def _run_yolo(model: YOLO, image: np.ndarray):
    results = model.predict(
        source=image,
        conf=settings.YOLO_CONFIDENCE_THRESHOLD,
        verbose=False,
    )
    if results and len(results[0].boxes) > 0:
        return results[0]
    return None


def detect_bone_region(image_path: str) -> Detection:
    """
    Runs YOLO on an X-ray image and returns the single highest-confidence
    detection (the primary bone/fracture region).

    Real-world uploads (phone photos of a film/screen) are often dark or
    low-contrast, which hurts detection confidence — so we first try an
    auto-brightness/contrast-enhanced version of the image. If that still
    finds nothing (e.g. the image was already well-lit and enhancement
    introduced artifacts), we fall back to the original raw image before
    giving up.

    Raises ValueError if nothing was detected above the confidence threshold
    on either attempt.
    """
    model = _get_model()

    original = cv2.imread(image_path)
    if original is None:
        raise ValueError(f"Could not read image file: {image_path}")

    enhanced = enhance_for_detection(original)

    result = _run_yolo(model, enhanced)

    if result is None:
        # Fall back to the raw, unenhanced image
        result = _run_yolo(model, original)

    if result is None:
        raise ValueError(
            "No bone/fracture region detected in this X-ray above the "
            f"confidence threshold ({settings.YOLO_CONFIDENCE_THRESHOLD}), "
            "even after brightness/contrast enhancement. Try a clearer image, "
            "or lower YOLO_CONFIDENCE_THRESHOLD in config.py."
        )

    boxes = result.boxes

    # Pick the highest-confidence box if multiple detected
    best_idx = int(np.argmax(boxes.conf.cpu().numpy()))
    xyxy = boxes.xyxy[best_idx].cpu().numpy().astype(int)
    conf = float(boxes.conf[best_idx].cpu().numpy())
    cls_id = int(boxes.cls[best_idx].cpu().numpy())
    class_name = model.names[cls_id]

    return Detection(
        bbox=(int(xyxy[0]), int(xyxy[1]), int(xyxy[2]), int(xyxy[3])),
        confidence=conf,
        class_name=class_name,
    )
