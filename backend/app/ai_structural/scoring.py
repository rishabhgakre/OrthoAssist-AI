"""
Structural Recovery Score (SRS) — pure math, no AI here.

Compares pre-op and post-op bone measurements and combines the improvement
into a single 0-100 score.

Formula (weights tunable — document your rationale in the report):
    SRS = 0.3 * gap_improvement + 0.3 * alignment_improvement + 0.4 * continuity_improvement
"""

from dataclasses import dataclass

from app.ai_structural.measurements import BoneMeasurements

WEIGHT_GAP = 0.3
WEIGHT_ALIGNMENT = 0.3
WEIGHT_CONTINUITY = 0.4


@dataclass
class SRSResult:
    gap_improvement_pct: float
    alignment_improvement_pct: float
    continuity_improvement_pct: float
    structural_recovery_score: float


def _gap_improvement(pre_gap: float, post_gap: float) -> float:
    """
    % reduction in fracture gap. If pre_gap is 0 (no visible gap even before
    surgery — e.g. a hairline fracture), we treat improvement as 100% if the
    post gap is also ~0, since there was nothing to close.
    """
    if pre_gap <= 0.01:
        return 100.0 if post_gap <= 0.01 else 0.0
    improvement = (pre_gap - post_gap) / pre_gap * 100.0
    return round(max(0.0, min(100.0, improvement)), 1)


def _pct_improvement(pre_value: float, post_value: float) -> float:
    """
    For metrics that are already 0-100 percentages (alignment, continuity),
    improvement is simply how much closer to 100 the post value got,
    relative to the room that was available to improve.
    """
    room_to_improve = 100.0 - pre_value
    if room_to_improve <= 0.01:
        return 100.0  # was already perfect pre-op
    improvement = (post_value - pre_value) / room_to_improve * 100.0
    return round(max(0.0, min(100.0, improvement)), 1)


def compute_srs(pre: BoneMeasurements, post: BoneMeasurements) -> SRSResult:
    gap_imp = _gap_improvement(pre.gap_mm, post.gap_mm)
    alignment_imp = _pct_improvement(pre.alignment_pct, post.alignment_pct)
    continuity_imp = _pct_improvement(pre.continuity_pct, post.continuity_pct)

    srs = (
        WEIGHT_GAP * gap_imp
        + WEIGHT_ALIGNMENT * alignment_imp
        + WEIGHT_CONTINUITY * continuity_imp
    )

    return SRSResult(
        gap_improvement_pct=gap_imp,
        alignment_improvement_pct=alignment_imp,
        continuity_improvement_pct=continuity_imp,
        structural_recovery_score=round(srs, 1),
    )
