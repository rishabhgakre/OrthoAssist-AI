from datetime import datetime
from typing import Optional, Dict, Any

from pydantic import BaseModel, EmailStr


# ---------- Auth ----------
class DoctorCreate(BaseModel):
    name: str
    email: EmailStr
    password: str


class DoctorOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ---------- Patient ----------
class PatientCreate(BaseModel):
    name: str
    age: int
    gender: str
    bone_type: str
    injury_notes: Optional[str] = None


class PatientOut(PatientCreate):
    id: int
    doctor_id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ---------- X-ray / Structural ----------
class XrayRecordOut(BaseModel):
    id: int
    patient_id: int

    pre_image_path: str
    post_image_path: str
    pre_annotated_path: Optional[str]
    post_annotated_path: Optional[str]

    pre_detection_confidence: Optional[float]
    post_detection_confidence: Optional[float]

    pre_gap_mm: Optional[float]
    pre_alignment_pct: Optional[float]
    pre_continuity_pct: Optional[float]
    pre_bone_angle_deg: Optional[float]

    post_gap_mm: Optional[float]
    post_alignment_pct: Optional[float]
    post_continuity_pct: Optional[float]
    post_bone_angle_deg: Optional[float]

    gap_improvement_pct: Optional[float]
    alignment_improvement_pct: Optional[float]
    continuity_improvement_pct: Optional[float]

    structural_recovery_score: Optional[float]
    raw_measurements: Optional[Dict[str, Any]]
    created_at: datetime

    class Config:
        from_attributes = True


# ---------- Gait / Functional ----------
class GaitRecordOut(BaseModel):
    id: int
    patient_id: int
    video_path: str
    annotated_video_path: Optional[str]
    walking_speed: Optional[float]
    cadence: Optional[float]
    stride_length: Optional[float]
    step_length: Optional[float]
    step_symmetry: Optional[float]
    knee_flexion: Optional[float]
    hip_movement: Optional[float]
    balance_score: Optional[float]
    functional_recovery_score: Optional[float]
    raw_measurements: Optional[Dict[str, Any]]
    created_at: datetime

    class Config:
        from_attributes = True


# ---------- CORI ----------
class CoriRecordOut(BaseModel):
    id: int
    patient_id: int
    xray_record_id: Optional[int]
    gait_record_id: Optional[int]
    structural_score: Optional[float]
    functional_score: Optional[float]
    weight_structural: Optional[float]
    weight_functional: Optional[float]
    cori_score: Optional[float]
    report_pdf_path: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class CoriComputeRequest(BaseModel):
    patient_id: int
    xray_record_id: int
    gait_record_id: Optional[int] = None  # required for lower-limb injuries, omit for upper-limb
    weight_structural: Optional[float] = None
    weight_functional: Optional[float] = None


class CoriResultOut(CoriRecordOut):
    """Extended response for /cori/compute — includes the explainability
    fields (summary, recommendation, flags) on top of the stored record."""
    recovery_stage: str
    summary: str
    recommendation: str
    flags: list[str]
    structural_detail: Optional[str] = None
    functional_detail: Optional[str] = None
