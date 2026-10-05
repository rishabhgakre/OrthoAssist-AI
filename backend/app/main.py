"""
OrthoAssist AI — backend entrypoint.

Run locally with:
    uvicorn app.main:app --reload --port 8000

Swagger docs auto-generated at:
    http://localhost:8000/docs
"""

import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from app.core.database import Base, engine, SessionLocal
from app.core.config import settings
from app.models import models  # noqa: F401  (needed so tables register with Base)
from app.routers import auth, patients, gait, xray, cori, reports

logger = logging.getLogger("orthoassist")

# Table creation/alteration in production now goes through Alembic
# (see backend/alembic/ and `alembic upgrade head`), not this call — that's
# what lets a later schema change (new column, renamed table, etc.) roll out
# to a deployed database safely and repeatably instead of relying on
# create_all(), which only ever adds missing tables and never alters
# existing ones. create_all() is kept here ONLY as a zero-setup convenience
# for a fresh local dev database; it's a safe no-op once Alembic has
# already created the same tables.
Base.metadata.create_all(bind=engine)

# Fail fast and loud rather than silently deploy insecurely: a wildcard
# CORS origin combined with allow_credentials is also rejected by browsers
# at runtime, so this would otherwise surface later as a confusing
# "it works locally but every request fails in prod" bug.
if settings.is_production and "*" in settings.cors_origins:
    raise RuntimeError(
        "ENVIRONMENT=production but FRONTEND_ORIGINS is unset or '*'. "
        "Set FRONTEND_ORIGINS to your real deployed frontend URL(s) "
        "(comma-separated for more than one), e.g. "
        "FRONTEND_ORIGINS=https://your-app.vercel.app"
    )

app = FastAPI(title=settings.PROJECT_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
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
# UPLOAD_DIR is the ONE knob to turn for deployment (e.g. "/data/uploads"
# pointed at a mounted persistent volume) — XRAY_DIR/VIDEO_DIR derive from
# it automatically (see core/config.py), so there's nothing else to keep in
# sync.
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.XRAY_DIR, exist_ok=True)
os.makedirs(settings.VIDEO_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")


@app.get("/")
def root():
    return {"status": "ok", "service": settings.PROJECT_NAME}


@app.get("/health")
def health():
    """Readiness check for Render/Kubernetes — confirms the process is up
    AND the database is actually reachable, not just that FastAPI started.
    Kubernetes should point both liveness and readiness probes here; a pod
    that can't reach its database shouldn't receive traffic."""
    db_ok = True
    try:
        db = SessionLocal()
        try:
            db.execute(text("SELECT 1"))
        finally:
            db.close()
    except Exception as exc:  # noqa: BLE001 — deliberately broad: any DB failure means "not ready"
        db_ok = False
        logger.warning("Health check: database unreachable: %s", exc)

    status_code = 200 if db_ok else 503
    body = {"status": "ok" if db_ok else "unavailable", "database": db_ok}
    return JSONResponse(content=body, status_code=status_code)
