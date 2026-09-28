import os

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_doctor
from app.core.cori_engine import compute_cori
from app.core.report_generator import generate_recovery_report
from app.models.models import Doctor, Patient, XrayRecord, GaitRecord, CoriRecord

router = APIRouter(prefix="/reports", tags=["Explainable AI Report"])

REPORTS_DIR = "reports"


@router.post("/{cori_id}/generate")
def generate_report(
    cori_id: int,
    db: Session = Depends(get_db),
    current_doctor: Doctor = Depends(get_current_doctor),
):
    """
    Generates the PDF report for an existing CORI record and saves it to
    disk. Returns the saved path — call GET /reports/{cori_id}/download
    afterward to actually retrieve the file.
    """
    cori_record = (
        db.query(CoriRecord)
        .join(Patient)
        .filter(CoriRecord.id == cori_id, Patient.doctor_id == current_doctor.id)
        .first()
    )
    if not cori_record:
        raise HTTPException(status_code=404, detail="CORI record not found")

    patient = db.query(Patient).filter(Patient.id == cori_record.patient_id).first()
    xray_record = db.query(XrayRecord).filter(XrayRecord.id == cori_record.xray_record_id).first()
    gait_record = db.query(GaitRecord).filter(GaitRecord.id == cori_record.gait_record_id).first()

    # ---- Rebuild the full explainability result (same logic as /cori/explain) ----
    structural_breakdown = None
    if xray_record:
        structural_breakdown = {
            "gap_improvement_pct": xray_record.gap_improvement_pct,
            "alignment_improvement_pct": xray_record.alignment_improvement_pct,
            "continuity_improvement_pct": xray_record.continuity_improvement_pct,
        }

    functional_breakdown = None
    if gait_record and gait_record.raw_measurements:
        functional_breakdown = {
            key: gait_record.raw_measurements[key]
            for key in (
                "walking_speed_score", "cadence_score", "symmetry_score",
                "balance_score", "knee_flexion_score",
            )
            if key in gait_record.raw_measurements
        }

    cori_result = compute_cori(
        structural_score=cori_record.structural_score,
        functional_score=cori_record.functional_score,
        weight_structural=cori_record.weight_structural,
        weight_functional=cori_record.weight_functional,
        structural_breakdown=structural_breakdown,
        functional_breakdown=functional_breakdown,
    )

    # ---- Generate the PDF ----
    os.makedirs(REPORTS_DIR, exist_ok=True)
    output_path = os.path.join(REPORTS_DIR, f"recovery_report_patient{patient.id}_cori{cori_id}.pdf")

    generate_recovery_report(
        output_path=output_path,
        patient=patient,
        xray_record=xray_record,
        gait_record=gait_record,
        cori_result=cori_result,
    )

    # ---- Save the path so it's retrievable later without regenerating ----
    cori_record.report_pdf_path = output_path
    db.commit()

    return {
        "message": "Report generated successfully",
        "cori_id": cori_id,
        "report_path": output_path,
        "download_url": f"/reports/{cori_id}/download",
    }


@router.get("/{cori_id}/download")
def download_report(
    cori_id: int,
    db: Session = Depends(get_db),
    current_doctor: Doctor = Depends(get_current_doctor),
):
    """Streams the previously-generated PDF report for download."""
    cori_record = (
        db.query(CoriRecord)
        .join(Patient)
        .filter(CoriRecord.id == cori_id, Patient.doctor_id == current_doctor.id)
        .first()
    )
    if not cori_record:
        raise HTTPException(status_code=404, detail="CORI record not found")

    if not cori_record.report_pdf_path or not os.path.exists(cori_record.report_pdf_path):
        raise HTTPException(
            status_code=404,
            detail="Report not generated yet — call POST /reports/{cori_id}/generate first.",
        )

    return FileResponse(
        path=cori_record.report_pdf_path,
        media_type="application/pdf",
        filename=os.path.basename(cori_record.report_pdf_path),
    )
