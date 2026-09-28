from datetime import datetime, timedelta
from typing import Optional

import bcrypt
from jose import jwt, JWTError

from app.core.config import settings

# NOTE: we use the `bcrypt` library directly instead of passlib's CryptContext.
# passlib's bcrypt backend detection is broken on bcrypt>=4.1 (it looks for a
# removed `__about__.__version__` attribute), which throws at runtime. Calling
# bcrypt directly avoids that whole problem and has one less dependency.
BCRYPT_MAX_BYTES = 72  # bcrypt silently ignores anything past 72 bytes


def hash_password(password: str) -> str:
    pw_bytes = password.encode("utf-8")[:BCRYPT_MAX_BYTES]
    hashed = bcrypt.hashpw(pw_bytes, bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    pw_bytes = plain_password.encode("utf-8")[:BCRYPT_MAX_BYTES]
    return bcrypt.checkpw(pw_bytes, hashed_password.encode("utf-8"))


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        return None
