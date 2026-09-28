"""
Database schema for OrthoAssist AI.

Relationships:
    Doctor 1---N Patient
    Patient 1---N XrayRecord      (structural recovery, pre/post comparison per assessment)
    Patient 1---N GaitRecord      (functional recovery, one per visit)
    Patient 1---N CoriRecord      (combined score, one per assessment/visit)
"""

from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, Float, DateTime, ForeignKey, Text, JSON
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class Doctor(Base):
    __tablename__ = "doctors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    patients = relationship("Patient", back_populates="doctor")


class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id"))
    name = Column(String, nullable=False)
    age = Column(Integer)
    gender = Column(String)
    bone_type = Column(String)       # e.g. "Tibia", "Femur"
    injury_notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    doctor = relationship("Doctor", back_populates="patients")
    xray_records = relationship("XrayRecord", back_populates="patient")
    gait_records = relationship("GaitRecord", back_populates="patient")
    cori_records = relationship("CoriRecord", back_populates="patient")


class XrayRecord(Base):
    """
    One structural-recovery assessment, comparing a pre-operative and
    post-operative (or two follow-up) X-rays of the SAME patient.

    Design rationale: public fracture datasets (FracAtlas etc.) don't provide
    matched pre/post pairs, so YOLO detection + segmentation are trained on
    public data, while the actual SRS comparison logic runs on the doctor's
    own paired uploads for a given patient.
    """
    __tablename__ = "xray_records"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))

    # ---- Raw uploads ----
    pre_image_path = Column(String, nullable=False)
    post_image_path = Column(String, nullable=False)

    # ---- Annotated overlays (for explainable AI report) ----
    pre_annotated_path = Column(String)
    post_annotated_path = Column(String)

    # ---- Detection ----
    pre_detection_confidence = Column(Float)
    post_detection_confidence = Column(Float)

    # ---- Pre-op measurements ----
    pre_gap_mm = Column(Float)
    pre_alignment_pct = Column(Float)
    pre_continuity_pct = Column(Float)
    pre_bone_angle_deg = Column(Float)

    # ---- Post-op measurements ----
    post_gap_mm = Column(Float)
    post_alignment_pct = Column(Float)
    post_continuity_pct = Column(Float)
    post_bone_angle_deg = Column(Float)

    # ---- Derived improvement metrics ----
    gap_improvement_pct = Column(Float)
    alignment_improvement_pct = Column(Float)
    continuity_improvement_pct = Column(Float)

    structural_recovery_score = Column(Float)  # combined 0-100 (SRS)

    raw_measurements = Column(JSON)      # full dict of everything for explainability
    created_at = Column(DateTime, default=datetime.utcnow)

    patient = relationship("Patient", back_populates="xray_records")


class GaitRecord(Base):
    """One functional-recovery assessment from a single walking-video upload."""
    __tablename__ = "gait_records"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))

    video_path = Column(String, nullable=False)
    annotated_video_path = Column(String)   # skeleton overlay for report

    walking_speed = Column(Float)        # m/s (normalized score too)
    cadence = Column(Float)              # steps/min
    stride_length = Column(Float)
    step_length = Column(Float)
    step_symmetry = Column(Float)        # 0-100
    knee_flexion = Column(Float)         # degrees
    hip_movement = Column(Float)         # degrees
    balance_score = Column(Float)        # 0-100

    functional_recovery_score = Column(Float)  # combined 0-100

    raw_measurements = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

    patient = relationship("Patient", back_populates="gait_records")


class CoriRecord(Base):
    """Composite Orthopedic Recovery Index — the project's core output."""
    __tablename__ = "cori_records"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    xray_record_id = Column(Integer, ForeignKey("xray_records.id"), nullable=True)
    gait_record_id = Column(Integer, ForeignKey("gait_records.id"), nullable=True)

    structural_score = Column(Float)
    functional_score = Column(Float)
    weight_structural = Column(Float)
    weight_functional = Column(Float)
    cori_score = Column(Float)

    report_pdf_path = Column(String)     # generated ReportLab PDF
    created_at = Column(DateTime, default=datetime.utcnow)

    patient = relationship("Patient", back_populates="cori_records")
