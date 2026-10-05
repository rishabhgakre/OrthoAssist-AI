"""
Central configuration for OrthoAssist AI backend.
Reads values from environment variables (with sane local defaults),
so nothing is hardcoded when you deploy.
"""

import os
from typing import List

from pydantic_settings import BaseSettings
from pydantic import field_validator


class Settings(BaseSettings):
    PROJECT_NAME: str = "OrthoAssist AI"

    # "development" or "production" — controls CORS strictness and whether
    # interactive API docs (/docs, /redoc) are exposed. Set via env var in
    # every real deployment; the default here is intentionally the safer
    # (more locked-down) of the two, so a forgotten env var fails closed,
    # not open.
    ENVIRONMENT: str = "production"

    # ---- Database ----
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/orthoassist"

    # ---- Auth ----
    SECRET_KEY: str = "CHANGE_THIS_TO_A_LONG_RANDOM_SECRET_IN_PRODUCTION"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 8  # 8 hour login session

    # ---- CORS ----
    # Comma-separated list of allowed frontend origins, e.g.
    # "https://orthoassist.vercel.app,https://app.orthoassist.ai" in prod.
    # Defaults to "*" ONLY so local dev (`uvicorn` + `vite dev`, different
    # ports) works out of the box with zero setup — this default is NOT
    # safe for production and ENVIRONMENT=production additionally refuses
    # to start with a wildcard origin (see main.py), so a deployment can't
    # silently go live mis-configured this way.
    FRONTEND_ORIGINS: str = "*"

    # ---- File storage ----
    # Only UPLOAD_DIR is ever set directly (by you, via env var, pointed at
    # wherever your deployment's persistent volume/disk is mounted —
    # e.g. "/data/uploads" in Docker/Kubernetes). XRAY_DIR and VIDEO_DIR
    # are *derived* from it below rather than being independent settings,
    # so there is no way for the physical write location and the path the
    # static file server looks in to silently drift apart.
    UPLOAD_DIR: str = "uploads"

    @property
    def XRAY_DIR(self) -> str:
        return os.path.join(self.UPLOAD_DIR, "xrays")

    @property
    def VIDEO_DIR(self) -> str:
        return os.path.join(self.UPLOAD_DIR, "videos")

    # ---- CORI weights (tunable per research findings) ----
    CORI_WEIGHT_STRUCTURAL: float = 0.5
    CORI_WEIGHT_FUNCTIONAL: float = 0.5

    # ---- Structural AI ----
    YOLO_WEIGHTS_PATH: str = "app/ai_structural/weights/best.pt"
    YOLO_CONFIDENCE_THRESHOLD: float = 0.25
    EXPECTED_BONE_ANGLE_DEG: float = 90.0  # reference alignment (straight bone axis)

    @field_validator("ENVIRONMENT")
    @classmethod
    def _validate_environment(cls, v: str) -> str:
        v = v.lower().strip()
        if v not in ("development", "production"):
            raise ValueError('ENVIRONMENT must be "development" or "production"')
        return v

    @property
    def cors_origins(self) -> List[str]:
        """Parsed, trimmed list form of FRONTEND_ORIGINS for CORSMiddleware."""
        return [o.strip() for o in self.FRONTEND_ORIGINS.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    class Config:
        env_file = ".env"


settings = Settings()
