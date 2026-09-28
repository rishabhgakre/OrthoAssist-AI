from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_doctor
from app.core.security import hash_password, verify_password, create_access_token
from app.models.models import Doctor
from app.schemas.schemas import DoctorCreate, DoctorOut, Token

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/signup", response_model=DoctorOut)
def signup(doctor_in: DoctorCreate, db: Session = Depends(get_db)):
    existing = db.query(Doctor).filter(Doctor.email == doctor_in.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    doctor = Doctor(
        name=doctor_in.name,
        email=doctor_in.email,
        hashed_password=hash_password(doctor_in.password),
    )
    db.add(doctor)
    db.commit()
    db.refresh(doctor)
    return doctor


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    doctor = db.query(Doctor).filter(Doctor.email == form_data.username).first()
    if not doctor or not verify_password(form_data.password, doctor.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    token = create_access_token(data={"sub": str(doctor.id)})
    return Token(access_token=token)


@router.get("/me", response_model=DoctorOut)
def get_me(current_doctor: Doctor = Depends(get_current_doctor)):
    """Returns the signed-in clinician's own profile — used by the frontend
    to show the real doctor name/initials in the sidebar instead of a
    hardcoded placeholder."""
    return current_doctor
