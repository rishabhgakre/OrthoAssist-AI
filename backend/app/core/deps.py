from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.models import Doctor

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def get_current_doctor(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> Doctor:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    doctor_id = payload.get("sub")
    if doctor_id is None:
        raise credentials_exception

    doctor = db.query(Doctor).filter(Doctor.id == int(doctor_id)).first()
    if doctor is None:
        raise credentials_exception
    return doctor
