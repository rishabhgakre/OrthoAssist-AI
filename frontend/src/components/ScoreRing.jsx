/**
 * Circular progress ring used for Structural / Functional / CORI headline
 * scores. Pure SVG (no chart lib needed for something this simple).
 */
export default function ScoreRing({
  value,
  size = 108,
  strokeWidth = 9,
  color = '#C9A66B',
  trackColor = 'rgba(0,0,0,0.08)',
  label,
  sublabel,
  valueClassName = 'fill-body',
  onDark = false,
}) {
  const v = value === null || value === undefined ? 0 : Math.max(0, Math.min(100, value))
  const radius = (size - strokeWidth) / 2
  const circumference = 2 * Math.PI * radius
  const offset = circumference - (v / 100) * circumference

  return (
    <div className="relative inline-flex items-center justify-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle
          cx={size / 2} cy={size / 2} r={radius}
          fill="none" stroke={onDark ? 'rgba(244,241,231,0.1)' : trackColor} strokeWidth={strokeWidth}
        />
        {value !== null && value !== undefined && (
          <circle
            cx={size / 2} cy={size / 2} r={radius}
            fill="none" stroke={color} strokeWidth={strokeWidth}
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            style={{ transition: 'stroke-dashoffset .8s cubic-bezier(.16,1,.3,1)' }}
          />
        )}
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className={`font-mono font-semibold ${onDark ? 'text-page' : 'text-body'}`} style={{ fontSize: size * 0.19 }}>
          {value === null || value === undefined ? '—' : `${value}%`}
        </span>
        {label && <span className={`text-[9.5px] mt-0.5 ${onDark ? 'text-[#8FA095]' : 'text-muted'}`} style={{ fontSize: size * 0.08 }}>{label}</span>}
      </div>
      {sublabel}
    </div>
  )
}
