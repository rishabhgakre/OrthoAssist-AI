export function initials(name = '') {
  return name
    .trim()
    .split(/\s+/)
    .map((p) => p[0])
    .join('')
    .slice(0, 2)
    .toUpperCase() || '?'
}

export function formatDate(value, opts) {
  if (!value) return '—'
  const d = new Date(value)
  return d.toLocaleDateString(undefined, opts || { day: 'numeric', month: 'short', year: 'numeric' })
}

export function formatDateTime(value) {
  if (!value) return '—'
  const d = new Date(value)
  return `${d.toLocaleDateString(undefined, { day: 'numeric', month: 'short', year: 'numeric' })}, ${d.toLocaleTimeString(undefined, { hour: 'numeric', minute: '2-digit' })}`
}

export function fmtNum(value, digits = 1, suffix = '') {
  if (value === null || value === undefined || Number.isNaN(value)) return '—'
  return `${Number(value).toFixed(digits)}${suffix}`
}

/** Recovery status tier — the single source of truth for score -> color/label
 * across dashboard, patient list, patient detail, and (mirrored) the PDF report. */
export function statusFromScore(score) {
  if (score === null || score === undefined) return 'pending'
  if (score >= 70) return 'malachite'
  if (score >= 50) return 'topaz'
  return 'garnet'
}

export function statusLabel(score) {
  if (score === null || score === undefined) return 'Pending'
  if (score >= 85) return 'Excellent'
  if (score >= 70) return 'Good'
  if (score >= 50) return 'Moderate'
  return 'Needs attention'
}

export const STATUS_STYLES = {
  malachite: { text: 'text-malachite', bg: 'bg-malachite-bg', dot: 'bg-malachite-bright', bar: 'bg-malachite-bright' },
  topaz: { text: 'text-topaz', bg: 'bg-topaz-bg', dot: 'bg-topaz-bright', bar: 'bg-topaz-bright' },
  garnet: { text: 'text-garnet', bg: 'bg-garnet-bg', dot: 'bg-garnet-bright', bar: 'bg-garnet-bright' },
  pending: { text: 'text-muted', bg: 'bg-card-alt', dot: 'bg-faint', bar: 'bg-faint' },
}

export function errMsg(err, fallback) {
  const detail = err?.response?.data?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail) && detail[0]?.msg) return detail[0].msg
  return fallback || 'Something went wrong. Please try again.'
}
