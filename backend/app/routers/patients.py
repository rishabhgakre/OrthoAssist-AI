from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_doctor
from app.models.models import Doctor, Patient
from app.schemas.schemas import PatientCreate, PatientOut

router = APIRouter(prefix="/patients", tags=["Patients"])


@router.post("/", response_model=PatientOut)
def create_patient(
    patient_in: PatientCreate,
    db: Session = Depends(get_db),
    current_doctor: Doctor = Depends(get_current_doctor),
):
    patient = Patient(**patient_in.model_dump(), doctor_id=current_doctor.id)
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


@router.get("/", response_model=List[PatientOut])
def list_patients(
    db: Session = Depends(get_db),
    current_doctor: Doctor = Depends(get_current_doctor),
):
    return db.query(Patient).filter(Patient.doctor_id == current_doctor.id).all()


@router.get("/{patient_id}", response_model=PatientOut)
def get_patient(
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
    return patient
