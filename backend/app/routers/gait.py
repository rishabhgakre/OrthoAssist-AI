import os
import shutil
import uuid
from dataclasses import asdict

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import get_current_doctor
from app.models.models import Doctor, Patient, GaitRecord
from app.schemas.schemas import GaitRecordOut
from app.ai_functional.gait_pipeline import extract_gait_features
from app.ai_functional.scoring import compute_functional_recovery_score

router = APIRouter(prefix="/gait", tags=["Functional AI (Gait)"])


@router.post("/analyze", response_model=GaitRecordOut)
def analyze_gait(
    patient_id: int = Form(...),
    patient_height_m: float = Form(None),
    video: UploadFile = File(...),
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

    # ---- Save uploaded video ----
    os.makedirs(settings.VIDEO_DIR, exist_ok=True)
    ext = os.path.splitext(video.filename)[1] or ".mp4"
    saved_name = f"{uuid.uuid4().hex}{ext}"
    saved_path = os.path.join(settings.VIDEO_DIR, saved_name)
    # Always store forward slashes: os.path.join uses "\" on Windows, which
    # breaks the /uploads/... URL the frontend builds from this path.
    saved_path = saved_path.replace(os.sep, "/")

    with open(saved_path, "wb") as f:
        shutil.copyfileobj(video.file, f)

    # ---- Run functional AI pipeline ----
    try:
        features = extract_gait_features(saved_path, known_height_m=patient_height_m)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    breakdown = compute_functional_recovery_score(features)

    # ---- Persist ----
    gait_record = GaitRecord(
        patient_id=patient_id,
        video_path=saved_path,
        walking_speed=features.walking_speed_mps,
        cadence=features.cadence_spm,
        stride_length=features.stride_length_m,
        step_length=features.step_length_m,
        step_symmetry=features.step_symmetry_pct,
        knee_flexion=features.avg_knee_flexion_deg,
        hip_movement=features.avg_hip_movement_deg,
        balance_score=features.balance_score_pct,
        functional_recovery_score=breakdown.functional_recovery_score,
        raw_measurements={**asdict(features), **asdict(breakdown)},
    )
    db.add(gait_record)
    db.commit()
    db.refresh(gait_record)
    return gait_record


@router.get("/patient/{patient_id}", response_model=list[GaitRecordOut])
def list_gait_records(
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
    return patient.gait_records