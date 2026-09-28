from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_doctor
from app.core.cori_engine import compute_cori
from app.core.bone_classification import is_gait_relevant
from app.models.models import Doctor, Patient, XrayRecord, GaitRecord, CoriRecord
from app.schemas.schemas import CoriRecordOut, CoriComputeRequest, CoriResultOut

router = APIRouter(prefix="/cori", tags=["CORI Engine"])


@router.post("/compute", response_model=CoriResultOut)
def compute_cori_score(
    request: CoriComputeRequest,
    db: Session = Depends(get_db),
    current_doctor: Doctor = Depends(get_current_doctor),
):
    # ---- Verify patient belongs to this doctor ----
    patient = (
        db.query(Patient)
        .filter(Patient.id == request.patient_id, Patient.doctor_id == current_doctor.id)
        .first()
    )
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    # ---- Fetch the structural (X-ray) record ----
    xray_record = (
        db.query(XrayRecord)
        .filter(XrayRecord.id == request.xray_record_id, XrayRecord.patient_id == request.patient_id)
        .first()
    )
    if not xray_record:
        raise HTTPException(status_code=404, detail="X-ray record not found for this patient")
    if xray_record.structural_recovery_score is None:
        raise HTTPException(
            status_code=422,
            detail="This X-ray record has no structural_recovery_score yet — "
                   "re-run /xray/analyze for this patient first.",
        )

    # ---- Determine whether gait analysis applies to this patient's injury ----
    gait_applicable = is_gait_relevant(patient.bone_type)

    gait_record = None
    if gait_applicable:
        # Lower-limb injury: gait_record_id is required, same as before.
        if not request.gait_record_id:
            raise HTTPException(
                status_code=422,
                detail=f"'{patient.bone_type}' is a lower-limb injury — gait analysis "
                       f"is required. Provide gait_record_id, or run /gait/analyze first.",
            )
        gait_record = (
            db.query(GaitRecord)
            .filter(GaitRecord.id == request.gait_record_id, GaitRecord.patient_id == request.patient_id)
            .first()
        )
        if not gait_record:
            raise HTTPException(status_code=404, detail="Gait record not found for this patient")
        if gait_record.functional_recovery_score is None:
            raise HTTPException(
                status_code=422,
                detail="This gait record has no functional_recovery_score yet — "
                       "re-run /gait/analyze for this patient first.",
            )
    elif request.gait_record_id:
        # Doctor supplied a gait_record_id for an upper-limb patient — this is
        # likely a mistake (gait isn't clinically meaningful here), so we warn
        # rather than silently ignoring what they explicitly provided.
        raise HTTPException(
            status_code=422,
            detail=f"'{patient.bone_type}' is an upper-limb injury — gait analysis is not "
                   f"clinically applicable and won't be used. Omit gait_record_id to compute "
                   f"a structural-only CORI score for this patient.",
        )

    # ---- Build sub-metric breakdowns for detailed explainability ----
    structural_breakdown = {
        "gap_improvement_pct": xray_record.gap_improvement_pct,
        "alignment_improvement_pct": xray_record.alignment_improvement_pct,
        "continuity_improvement_pct": xray_record.continuity_improvement_pct,
    }
    functional_breakdown = None
    functional_score = None
    gait_not_applicable_reason = None

    if gait_record:
        functional_score = gait_record.functional_recovery_score
        functional_breakdown = {}
        if gait_record.raw_measurements:
            for key in (
                "walking_speed_score", "cadence_score", "symmetry_score",
                "balance_score", "knee_flexion_score",
            ):
                if key in gait_record.raw_measurements:
                    functional_breakdown[key] = gait_record.raw_measurements[key]
    elif not gait_applicable:
        gait_not_applicable_reason = (
            f"Gait analysis is not clinically meaningful for {patient.bone_type} injuries, "
            f"since walking gait has no bearing on upper-limb recovery."
        )

    # ---- Compute CORI with full explainability ----
    result = compute_cori(
        structural_score=xray_record.structural_recovery_score,
        functional_score=functional_score,
        weight_structural=request.weight_structural,
        weight_functional=request.weight_functional,
        structural_breakdown=structural_breakdown,
        functional_breakdown=functional_breakdown,
        gait_not_applicable_reason=gait_not_applicable_reason,
    )

    # ---- Persist ----
    cori_record = CoriRecord(
        patient_id=request.patient_id,
        xray_record_id=xray_record.id,
        gait_record_id=gait_record.id if gait_record else None,
        structural_score=xray_record.structural_recovery_score,
        functional_score=functional_score,
        weight_structural=result.weight_structural,
        weight_functional=result.weight_functional,
        cori_score=result.cori_score,
    )
    db.add(cori_record)
    db.commit()
    db.refresh(cori_record)

    # Combine the stored DB record with the freshly-computed explainability
    # fields (summary/recommendation/flags aren't stored as separate columns
    # since they're deterministically derivable from the scores — this keeps
    # the DB schema lean while still returning full explainability to the caller).
    return CoriResultOut(
        **CoriRecordOut.model_validate(cori_record).model_dump(),
        recovery_stage=result.recovery_stage,
        summary=result.summary,
        recommendation=result.recommendation,
        flags=result.flags,
        structural_detail=result.structural_detail,
        functional_detail=result.functional_detail,
    )


@router.get("/patient/{patient_id}", response_model=list[CoriRecordOut])
def list_cori_records(
    patient_id: int,
    db: Session = Depends(get_db),
    current_doctor: Doctor = Depends(get_current_doctor),
):
    """Returns the full CORI history for a patient — useful for trend charts."""
    patient = (
        db.query(Patient)
        .filter(Patient.id == patient_id, Patient.doctor_id == current_doctor.id)
        .first()
    )
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient.cori_records


@router.get("/{cori_id}/explain")
def explain_cori_score(
    cori_id: int,
    db: Session = Depends(get_db),
    current_doctor: Doctor = Depends(get_current_doctor),
):
    """
    Returns the full explainable breakdown (summary, recommendation, flags)
    for an existing CORI record — recomputed on the fly from the stored
    scores, since the explanation logic is deterministic.
    """
    cori_record = (
        db.query(CoriRecord)
        .join(Patient)
        .filter(CoriRecord.id == cori_id, Patient.doctor_id == current_doctor.id)
        .first()
    )
    if not cori_record:
        raise HTTPException(status_code=404, detail="CORI record not found")

    # Fetch the linked patient/X-ray/gait records to rebuild sub-metric breakdowns
    patient = db.query(Patient).filter(Patient.id == cori_record.patient_id).first()
    xray_record = db.query(XrayRecord).filter(XrayRecord.id == cori_record.xray_record_id).first()
    gait_record = None
    if cori_record.gait_record_id:
        gait_record = db.query(GaitRecord).filter(GaitRecord.id == cori_record.gait_record_id).first()

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

    gait_not_applicable_reason = None
    if cori_record.functional_score is None and patient and not is_gait_relevant(patient.bone_type):
        gait_not_applicable_reason = (
            f"Gait analysis is not clinically meaningful for {patient.bone_type} injuries, "
            f"since walking gait has no bearing on upper-limb recovery."
        )

    result = compute_cori(
        structural_score=cori_record.structural_score,
        functional_score=cori_record.functional_score,
        weight_structural=cori_record.weight_structural,
        weight_functional=cori_record.weight_functional,
        structural_breakdown=structural_breakdown,
        functional_breakdown=functional_breakdown,
        gait_not_applicable_reason=gait_not_applicable_reason,
    )

    return {
        "cori_id": cori_record.id,
        "patient_id": cori_record.patient_id,
        "cori_score": result.cori_score,
        "recovery_stage": result.recovery_stage,
        "summary": result.summary,
        "recommendation": result.recommendation,
        "flags": result.flags,
        "structural_detail": result.structural_detail,
        "functional_detail": result.functional_detail,
        "structural_score": cori_record.structural_score,
        "functional_score": cori_record.functional_score,
        "weight_structural": cori_record.weight_structural,
        "weight_functional": cori_record.weight_functional,
    }
