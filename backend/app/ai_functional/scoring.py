"""
Turns raw gait measurements into a 0-100 Functional Recovery Score (FRS).

Clinical reference ranges below are reasonable literature-informed defaults
for a healthy adult gait — for your research report, cite normative gait
studies to justify (or tune) these numbers, since they directly affect FRS.
"""

from dataclasses import dataclass

from app.ai_functional.gait_pipeline import GaitFeatures

# Reference "healthy" values — used to normalize each metric to 0-100
NORMAL_WALKING_SPEED_MPS = 1.2      # ~1.2-1.4 m/s is typical healthy adult speed
NORMAL_CADENCE_SPM = 110.0          # steps/min
NORMAL_KNEE_FLEXION_DEG = 60.0      # peak swing-phase knee flexion reference


def _score_against_reference(value: float, reference: float, tolerance: float = 0.4) -> float:
    """
    Scores how close `value` is to `reference`, as a percentage.
    tolerance = fraction of reference allowed as deviation before score hits 0.
    """
    if reference == 0:
        return 0.0
    deviation_ratio = abs(value - reference) / reference
    score = max(0.0, 100.0 * (1 - deviation_ratio / tolerance))
    return min(score, 100.0)


@dataclass
class FunctionalScoreBreakdown:
    walking_speed_score: float
    cadence_score: float
    symmetry_score: float
    balance_score: float
    knee_flexion_score: float
    functional_recovery_score: float


def compute_functional_recovery_score(features: GaitFeatures) -> FunctionalScoreBreakdown:
    # Walking speed uses a wider tolerance (1.0, vs the 0.4 default) than
    # the other metrics. This is deliberate: patients recovering from a
    # fracture routinely walk well below the "healthy adult" reference
    # speed, especially early on — with the default 0.4 tolerance, anyone
    # below ~72% of reference speed (0.72 m/s) scores a flat 0, making it
    # impossible to distinguish a patient improving from 0.2 -> 0.4 -> 0.6
    # m/s across visits from one who genuinely cannot walk. A tolerance of
    # 1.0 makes the score scale smoothly from 0 (not walking) to 100
    # (healthy speed), so incremental recovery is actually visible.

    walking_speed_score = _score_against_reference(
        features.walking_speed_mps,
        NORMAL_WALKING_SPEED_MPS,
        tolerance=1.0,
    )

    cadence_score = _score_against_reference(
        features.cadence_spm,
        NORMAL_CADENCE_SPM,
        tolerance=1.0,
    )

    knee_flexion_score = _score_against_reference(
        features.avg_knee_flexion_deg,
        NORMAL_KNEE_FLEXION_DEG,
        tolerance=1.0,
    )
    symmetry_score = features.step_symmetry_pct       # already 0-100
    balance_score = features.balance_score_pct        # already 0-100

    # Weighted combination — tune these weights based on your dataset/validation
    weights = {
        "speed": 0.25,
        "cadence": 0.15,
        "symmetry": 0.25,
        "balance": 0.20,
        "knee": 0.15,
    }

    frs = (
        weights["speed"] * walking_speed_score
        + weights["cadence"] * cadence_score
        + weights["symmetry"] * symmetry_score
        + weights["balance"] * balance_score
        + weights["knee"] * knee_flexion_score
    )

    return FunctionalScoreBreakdown(
        walking_speed_score=round(walking_speed_score, 1),
        cadence_score=round(cadence_score, 1),
        symmetry_score=round(symmetry_score, 1),
        balance_score=round(balance_score, 1),
        knee_flexion_score=round(knee_flexion_score, 1),
        functional_recovery_score=round(frs, 1),
    )