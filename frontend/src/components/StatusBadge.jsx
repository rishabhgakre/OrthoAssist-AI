import { statusFromScore, statusLabel, STATUS_STYLES } from '../lib/format'

export default function StatusBadge({ score, className = '' }) {
  const status = statusFromScore(score)
  const styles = STATUS_STYLES[status]

  return (
    <span
      className={`inline-flex items-center gap-1.5 text-[10.5px] px-2.5 py-1 rounded-full font-semibold ${styles.text} ${styles.bg} ${className}`}
    >
      <span className={`w-1.5 h-1.5 rounded-full ${styles.dot}`} />
      {statusLabel(score)}
    </span>
  )
}
