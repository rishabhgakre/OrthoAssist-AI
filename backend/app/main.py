"""
OrthoAssist AI — backend entrypoint.

Run locally with:
    uvicorn app.main:app --reload --port 8000

Swagger docs auto-generated at:
    http://localhost:8000/docs
"""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.database import Base, engine
from app.core.config import settings
from app.models import models  # noqa: F401  (needed so tables register with Base)
from app.routers import auth, patients, gait, xray, cori, reports

# Creates tables if they don't exist yet.
# For real project work, switch to Alembic migrations (already in requirements.txt).
Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.PROJECT_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten this to your React URL before deployment
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(patients.router)
app.include_router(gait.router)
app.include_router(xray.router)
app.include_router(cori.router)
app.include_router(reports.router)

# ---- Serve uploaded X-rays / videos so the frontend can render them ----
# XrayRecord.pre_image_path etc. are stored as "uploads/xrays/<file>", i.e.
# relative to settings.UPLOAD_DIR's parent — mounting UPLOAD_DIR at
# "/uploads" means those stored paths double as URL paths directly.
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.XRAY_DIR, exist_ok=True)
os.makedirs(settings.VIDEO_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")


@app.get("/")
def root():
    return {"status": "ok", "service": settings.PROJECT_NAME}
