"""
CORI Engine — Composite Orthopedic Recovery Index.

This is the project's core innovation: combining Structural Recovery Score
(from X-ray analysis) and Functional Recovery Score (from gait analysis)
into one unified, explainable recovery assessment.

    CORI = weight_structural * SRS + weight_functional * FRS

But a raw number isn't useful to a doctor on its own — this module also
generates a plain-language explanation and recommendation, because a doctor
needs to understand WHY the score is what it is, not just see a number.
"""

from dataclasses import dataclass
from typing import Optional, Dict

from app.core.config import settings


@dataclass
class CoriResult:
    cori_score: float
    weight_structural: float
    weight_functional: float
    recovery_stage: str          # short category label
    summary: str                 # 1-2 sentence plain-language explanation
    recommendation: str          # what the doctor should consider doing next
    flags: list                  # specific things worth the doctor's attention
    structural_detail: Optional[str] = None   # which structural sub-metric(s) drove the score
    functional_detail: Optional[str] = None   # which functional sub-metric(s) drove the score


# Human-readable labels for each sub-metric, used when naming specific
# drivers in the explanation text.
STRUCTURAL_METRIC_LABELS = {
    "gap_improvement_pct": "fracture gap closure",
    "alignment_improvement_pct": "bone alignment",
    "continuity_improvement_pct": "bone continuity",
}

FUNCTIONAL_METRIC_LABELS = {
    "walking_speed_score": "walking speed",
    "cadence_score": "cadence (step rate)",
    "symmetry_score": "step symmetry",
    "balance_score": "balance",
    "knee_flexion_score": "knee flexion",
}


def _describe_breakdown(breakdown: Dict[str, float], labels: Dict[str, str]) -> Optional[str]:
    """
    Given a dict of sub-metric name -> score (0-100), identifies the
    weakest and strongest contributors and describes them in plain language.
    Returns None if there isn't enough data to say anything meaningful.
    """
    available = {k: v for k, v in breakdown.items() if k in labels and v is not None}
    if len(available) < 2:
        return None

    weakest_key = min(available, key=available.get)
    strongest_key = max(available, key=available.get)
    weakest_val = available[weakest_key]
    strongest_val = available[strongest_key]

    if weakest_key == strongest_key:
        return None

    weakest_label = labels[weakest_key]
    strongest_label = labels[strongest_key]

    # Only worth calling out if there's a meaningful spread — otherwise
    # everything is roughly even and naming "weakest" is just noise.
    if strongest_val - weakest_val < 15:
        return "All measured sub-components are fairly consistent (within a narrow range)."

    # Scale the language to how concerning the weakest value ACTUALLY is,
    # not just its rank — a "weakest" score of 84% is still good and
    # shouldn't be described the same way as a genuinely low 40%.
    if weakest_val < 50:
        concern_phrase = "notably low — recommend focused clinical attention"
    elif weakest_val < 75:
        concern_phrase = "comparatively lower — worth continued monitoring"
    else:
        concern_phrase = "still solid, though relatively the lowest of the group"

    return (
        f"The strongest contributor is {strongest_label} ({strongest_val}%); "
        f"{weakest_label} ({weakest_val}%) is {concern_phrase}."
    )


# Score bands — tune these based on clinical input if available; documented
# here so the reasoning is auditable, not a black box.
def _recovery_stage(cori: float) -> str:
    if cori >= 85:
        return "Excellent Recovery"
    elif cori >= 70:
        return "Good Recovery"
    elif cori >= 50:
        return "Moderate Recovery"
    else:
        return "Early / Limited Recovery"


def compute_cori(
    structural_score: float,
    functional_score: Optional[float] = None,
    weight_structural: Optional[float] = None,
    weight_functional: Optional[float] = None,
    structural_breakdown: Optional[Dict[str, float]] = None,
    functional_breakdown: Optional[Dict[str, float]] = None,
    gait_not_applicable_reason: Optional[str] = None,
) -> CoriResult:
    """
    Computes the CORI score and generates an explainable summary.

    Weights default to config values (0.5/0.5) but can be overridden per
    request — e.g. a doctor may want to weight structural higher shortly
    after surgery, and functional higher during later physiotherapy stages.

    structural_breakdown / functional_breakdown: optional dicts of the
    underlying sub-metric scores (e.g. gap_improvement_pct, symmetry_score).
    When provided, the explanation names the SPECIFIC sub-metric driving a
    low or high score, instead of only reporting the aggregate number.

    functional_score=None means gait analysis isn't being used for this
    assessment — either because it wasn't performed yet, or (see
    gait_not_applicable_reason) because it isn't clinically meaningful for
    this injury (e.g. an upper-limb fracture, where walking gait has no
    bearing on hand/wrist recovery). In either case, CORI falls back to
    structural score alone rather than silently treating a missing
    functional score as zero.
    """
    if functional_score is None:
        cori = round(structural_score, 1)
        stage = _recovery_stage(cori)

        structural_detail = None
        if structural_breakdown:
            structural_detail = _describe_breakdown(structural_breakdown, STRUCTURAL_METRIC_LABELS)

        flags = []
        if gait_not_applicable_reason:
            flags.append(
                f"Functional (gait) analysis was not included in this score: "
                f"{gait_not_applicable_reason} CORI reflects structural recovery only."
            )
        else:
            flags.append(
                "No functional (gait) assessment is linked to this CORI yet — "
                "score reflects structural recovery only."
            )

        if structural_score < 50:
            flags.append(
                "Structural recovery score is low — recommend closer monitoring of "
                "bone healing progress, and confirm this against direct radiologist review."
            )

        summary = (
            f"This patient's Composite Orthopedic Recovery Index is {cori}% "
            f"({stage}), based on Structural Recovery Score alone "
            f"({structural_score}%)."
        )

        recommendation = _generate_structural_only_recommendation(cori, structural_score, structural_detail)

        return CoriResult(
            cori_score=cori,
            weight_structural=1.0,
            weight_functional=0.0,
            recovery_stage=stage,
            summary=summary,
            recommendation=recommendation,
            flags=flags,
            structural_detail=structural_detail,
            functional_detail=None,
        )

    w_struct = weight_structural if weight_structural is not None else settings.CORI_WEIGHT_STRUCTURAL
    w_func = weight_functional if weight_functional is not None else settings.CORI_WEIGHT_FUNCTIONAL

    # Normalize weights in case they don't sum to 1 (defensive — avoids a
    # silently wrong score if a caller passes e.g. 0.7/0.7 by mistake)
    total_weight = w_struct + w_func
    if total_weight <= 0:
        raise ValueError("Structural and functional weights must sum to a positive number.")
    w_struct = w_struct / total_weight
    w_func = w_func / total_weight

    cori = round(w_struct * structural_score + w_func * functional_score, 1)
    stage = _recovery_stage(cori)

    # ---- Explainability: WHY this score, in plain language ----
    gap = round(structural_score - functional_score, 1)
    flags = []

    if abs(gap) >= 20:
        if gap > 0:
            flags.append(
                f"Structural healing ({structural_score}%) is notably ahead of "
                f"functional recovery ({functional_score}%) — the bone has healed "
                f"well, but the patient's walking/mobility hasn't caught up yet. "
                f"This is common and usually means physiotherapy needs more focus."
            )
        else:
            flags.append(
                f"Functional recovery ({functional_score}%) is ahead of structural "
                f"healing ({structural_score}%) — the patient is moving reasonably "
                f"well, but the bone itself may still need monitoring. Verify "
                f"structural findings before increasing activity load."
            )

    if structural_score < 50:
        flags.append(
            "Structural recovery score is low — recommend closer monitoring of "
            "bone healing progress, and confirm this against direct radiologist review."
        )
    if functional_score < 50:
        flags.append(
            "Functional recovery score is low — gait shows significant deviation "
            "from normal walking patterns; consider physiotherapy intensity review."
        )

    # ---- Detailed sub-metric explanations (the "which specific thing?" layer) ----
    structural_detail = None
    functional_detail = None
    if structural_breakdown:
        structural_detail = _describe_breakdown(structural_breakdown, STRUCTURAL_METRIC_LABELS)
    if functional_breakdown:
        functional_detail = _describe_breakdown(functional_breakdown, FUNCTIONAL_METRIC_LABELS)

    summary = (
        f"This patient's Composite Orthopedic Recovery Index is {cori}% "
        f"({stage}), combining a Structural Recovery Score of {structural_score}% "
        f"and a Functional Recovery Score of {functional_score}%."
    )

    recommendation = _generate_recommendation(
        cori, structural_score, functional_score, structural_detail, functional_detail
    )

    return CoriResult(
        cori_score=cori,
        weight_structural=round(w_struct, 2),
        weight_functional=round(w_func, 2),
        recovery_stage=stage,
        summary=summary,
        recommendation=recommendation,
        flags=flags,
        structural_detail=structural_detail,
        functional_detail=functional_detail,
    )


def _generate_structural_only_recommendation(
    cori: float, structural_score: float, structural_detail: Optional[str] = None
) -> str:
    """
    Recommendation generator for upper-limb (structural-only) cases. Kept
    separate from _generate_recommendation() so the language never mentions
    "functional measures" for a patient where gait wasn't assessed at all —
    reusing the combined-mode text here previously produced a misleading
    recommendation ("strong across both structural and functional measures")
    even when functional was never evaluated.
    """
    if cori >= 85:
        base = (
            "Structural healing indicators are strong. Consider standard follow-up "
            "interval; discharge from active monitoring may be appropriate per "
            "clinical judgment."
        )
    elif cori >= 70:
        base = (
            "Structural recovery is progressing well. Continue current treatment "
            "plan and monitor via follow-up imaging as scheduled."
        )
    elif cori >= 50:
        base = (
            "Structural recovery is progressing but below optimal pace. Consider "
            "a follow-up X-ray sooner than the standard interval to track trajectory."
        )
    else:
        base = (
            "Structural recovery indicators are low. Recommend closer clinical "
            "review — consider whether complications (delayed union, malalignment, "
            "hardware issues) should be investigated."
        )

    if structural_detail:
        base += f" {structural_detail}"

    return base


def _generate_recommendation(
    cori: float,
    structural: float,
    functional: float,
    structural_detail: Optional[str] = None,
    functional_detail: Optional[str] = None,
) -> str:
    """
    Generates a plain-language next-step suggestion. This is decision
    SUPPORT, not a diagnosis or prescription — always frame it as something
    for the doctor to consider, not an instruction, since the doctor makes
    the actual clinical call.
    """
    if cori >= 85:
        base = (
            "Recovery indicators are strong across both structural and functional "
            "measures. Consider standard follow-up interval; discharge from active "
            "monitoring may be appropriate per clinical judgment."
        )
    elif cori >= 70:
        if functional < structural - 15:
            base = (
                "Bone healing looks solid. Consider increasing physiotherapy "
                "intensity/frequency to help functional recovery catch up."
            )
            if functional_detail:
                base += f" {functional_detail}"
        elif structural < functional - 15:
            base = (
                "Gait/mobility is progressing well. Recommend a follow-up X-ray "
                "to confirm structural healing is keeping pace before increasing "
                "activity levels."
            )
            if structural_detail:
                base += f" {structural_detail}"
        else:
            base = "Continue current treatment plan; recovery is progressing as expected."
    elif cori >= 50:
        base = (
            "Recovery is progressing but below optimal pace. Recommend continued "
            "physiotherapy, and consider a follow-up assessment sooner than the "
            "standard interval to track trajectory."
        )
    else:
        base = (
            "Recovery indicators are low. Recommend closer clinical review — "
            "consider whether complications (delayed union, infection, "
            "non-compliance with physiotherapy) should be investigated."
        )

    return base
