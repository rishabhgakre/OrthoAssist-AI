"""
Bone Classification — determines whether functional (gait) analysis is
clinically applicable for a given injury.

Rationale: gait analysis measures WALKING. It is only meaningful for
lower-limb injuries (the leg physically involved in walking). A wrist or
hand fracture has essentially no effect on how a patient walks — including
gait in that patient's CORI score would not just be uninformative, it would
be actively misleading (a normal gait score could mask a poorly-healed hand).

So:
    Lower-limb injury  -> CORI combines Structural + Functional (as designed)
    Upper-limb injury  -> CORI reflects Structural recovery only
"""

# Bones/regions where gait meaningfully reflects recovery
LOWER_LIMB_BONES = {
    "tibia", "fibula", "femur", "ankle", "foot", "hip", "pelvis",
    "knee", "patella", "lower leg", "leg",
}

# Bones/regions where walking gait is not a meaningful recovery indicator
UPPER_LIMB_BONES = {
    "hand", "wrist", "forearm", "radius", "ulna", "humerus",
    "shoulder", "elbow", "finger", "thumb", "arm", "clavicle", "collarbone",
}


def is_gait_relevant(bone_type: str) -> bool:
    """
    Returns True if gait/functional analysis is clinically meaningful for
    this bone type, False otherwise.

    Defaults to True (gait-relevant) for unrecognized bone types, since
    that preserves current behavior rather than silently dropping the
    functional score for a typo or an unlisted lower-limb bone — but logs
    are worth checking if this default gets hit often in practice.
    """
    if not bone_type:
        return True

    normalized = bone_type.strip().lower()

    if normalized in UPPER_LIMB_BONES:
        return False
    if normalized in LOWER_LIMB_BONES:
        return True

    # Partial match fallback (e.g. "Right Wrist", "Distal Radius")
    for upper_bone in UPPER_LIMB_BONES:
        if upper_bone in normalized:
            return False
    for lower_bone in LOWER_LIMB_BONES:
        if lower_bone in normalized:
            return True

    return True  # unrecognized -> default to gait-relevant (preserves old behavior)
