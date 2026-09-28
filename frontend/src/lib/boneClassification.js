/**
 * Mirrors backend/app/core/bone_classification.py so the frontend can show
 * the right hints/forms *before* hitting the API (e.g. on the New Patient
 * form), while the backend remains the actual source of truth enforced at
 * assessment time.
 */
const UPPER_LIMB_BONES = [
  'hand', 'wrist', 'forearm', 'radius', 'ulna', 'humerus',
  'shoulder', 'elbow', 'finger', 'thumb', 'arm', 'clavicle', 'collarbone',
]

const LOWER_LIMB_BONES = [
  'tibia', 'fibula', 'femur', 'ankle', 'foot', 'hip', 'pelvis',
  'knee', 'patella', 'lower leg', 'leg',
]

export function isGaitRelevant(boneType) {
  if (!boneType) return true
  const normalized = boneType.trim().toLowerCase()
  if (UPPER_LIMB_BONES.includes(normalized)) return false
  if (LOWER_LIMB_BONES.includes(normalized)) return true
  if (UPPER_LIMB_BONES.some((b) => normalized.includes(b))) return false
  if (LOWER_LIMB_BONES.some((b) => normalized.includes(b))) return true
  return true
}

export const BONE_TYPE_GROUPS = [
  {
    label: 'Lower limb · gait assessment applies',
    types: ['Tibia', 'Fibula', 'Femur', 'Ankle', 'Foot', 'Hip', 'Knee'],
  },
  {
    label: 'Upper limb · structural only',
    types: ['Wrist', 'Hand', 'Forearm', 'Humerus', 'Shoulder', 'Elbow', 'Clavicle'],
  },
]

export const BONE_TYPES = BONE_TYPE_GROUPS.flatMap((g) => g.types)
