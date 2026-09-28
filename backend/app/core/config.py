"""
Central configuration for OrthoAssist AI backend.
Reads values from environment variables (with sane local defaults),
so nothing is hardcoded when you deploy.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "OrthoAssist AI"

    # ---- Database ----
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/orthoassist"

    # ---- Auth ----
    SECRET_KEY: str = "CHANGE_THIS_TO_A_LONG_RANDOM_SECRET_IN_PRODUCTION"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 8  # 8 hour login session

    # ---- File storage ----
    UPLOAD_DIR: str = "uploads"
    XRAY_DIR: str = "uploads/xrays"
    VIDEO_DIR: str = "uploads/videos"

    # ---- CORI weights (tunable per research findings) ----
    CORI_WEIGHT_STRUCTURAL: float = 0.5
    CORI_WEIGHT_FUNCTIONAL: float = 0.5

    # ---- Structural AI ----
    YOLO_WEIGHTS_PATH: str = "app/ai_structural/weights/best.pt"
    YOLO_CONFIDENCE_THRESHOLD: float = 0.25
    EXPECTED_BONE_ANGLE_DEG: float = 90.0  # reference alignment (straight bone axis)

    class Config:
        env_file = ".env"


settings = Settings()
