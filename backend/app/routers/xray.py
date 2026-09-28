import os
import shutil
import uuid

import cv2
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import get_current_doctor
from app.models.models import Doctor, Patient, XrayRecord
from app.schemas.schemas import XrayRecordOut
from app.ai_structural.detection import detect_bone_region
from app.ai_structural.segmentation import segment_bone
from app.ai_structural.measurements import measure_bone, BoneMeasurements
from app.ai_structural.scoring import compute_srs

router = APIRouter(prefix="/xray", tags=["Structural AI (X-ray)"])


def _save_upload(upload: UploadFile, directory: str) -> str:
    os.makedirs(directory, exist_ok=True)
    ext = os.path.splitext(upload.filename)[1] or ".jpg"
    saved_name = f"{uuid.uuid4().hex}{ext}"
    saved_path = os.path.join(directory, saved_name)
    # Always store forward slashes: os.path.join uses "\" on Windows, which
    # breaks the /uploads/... URL the frontend builds from this path.
    saved_path = saved_path.replace(os.sep, "/")
    with open(saved_path, "wb") as f:
        shutil.copyfileobj(upload.file, f)
    return saved_path


def _run_structural_pipeline(image_path: str) -> tuple[BoneMeasurements, float]:
    """
    Runs detection -> segmentation -> measurement for ONE X-ray image.
    Returns (measurements, detection_confidence).
    """
    detection = detect_bone_region(image_path)

    image = cv2.imread(image_path)
    if image is None:
        raise HTTPException(status_code=422, detail=f"Could not read image: {image_path}")

    segmentation = segment_bone(image, detection.bbox)
    measurements = measure_bone(segmentation)

    return measurements, detection.confidence


@router.post("/analyze", response_model=XrayRecordOut)
def analyze_xray(
    patient_id: int = Form(...),
    pre_image: UploadFile = File(..., description="Pre-operative X-ray"),
    post_image: UploadFile = File(..., description="Post-operative (or follow-up) X-ray"),
    db: Session = Depends(get_db),
    current_doctor: Doctor = Depends(get_current_doctor),
):
    patient = (
        db.query(Patient)
        .filter(Patient.id == patient_id, Patient.doctor_id == current_doctor.id)
        .first()
    )
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    # ---- Save both uploads ----
    pre_path = _save_upload(pre_image, settings.XRAY_DIR)
    post_path = _save_upload(post_image, settings.XRAY_DIR)

    # ---- Run the structural pipeline on each image ----
    try:
        pre_measure, pre_conf = _run_structural_pipeline(pre_path)
        post_measure, post_conf = _run_structural_pipeline(post_path)
    except FileNotFoundError as e:
        # YOLO weights not trained/placed yet — clear, actionable error
        raise HTTPException(status_code=503, detail=str(e))
    except ValueError as e:
        # No detection / segmentation failure on a specific image
        raise HTTPException(status_code=422, detail=str(e))

    # ---- Compare pre vs post -> SRS ----
    srs_result = compute_srs(pre_measure, post_measure)

    # ---- Persist ----
    xray_record = XrayRecord(
        patient_id=patient_id,
        pre_image_path=pre_path,
        post_image_path=post_path,
        pre_detection_confidence=pre_conf,
        post_detection_confidence=post_conf,
        pre_gap_mm=pre_measure.gap_mm,
        pre_alignment_pct=pre_measure.alignment_pct,
        pre_continuity_pct=pre_measure.continuity_pct,
        pre_bone_angle_deg=pre_measure.bone_angle_deg,
        post_gap_mm=post_measure.gap_mm,
        post_alignment_pct=post_measure.alignment_pct,
        post_continuity_pct=post_measure.continuity_pct,
        post_bone_angle_deg=post_measure.bone_angle_deg,
        gap_improvement_pct=srs_result.gap_improvement_pct,
        alignment_improvement_pct=srs_result.alignment_improvement_pct,
        continuity_improvement_pct=srs_result.continuity_improvement_pct,
        structural_recovery_score=srs_result.structural_recovery_score,
        raw_measurements={
            "pre": pre_measure.__dict__,
            "post": post_measure.__dict__,
            "srs": srs_result.__dict__,
        },
    )
    db.add(xray_record)
    db.commit()
    db.refresh(xray_record)
    return xray_record


@router.get("/patient/{patient_id}", response_model=list[XrayRecordOut])
def list_xray_records(
    patient_id: int,
    db: Session = Depends(get_db),
    current_doctor: Doctor = Depends(get_current_doctor),
):
    patient = (
        db.query(Patient)
        .filter(Patient.id == patient_id, Patient.doctor_id == current_doctor.id)
        .first()
    )
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient.xray_records