import { IconCheck } from '@tabler/icons-react'

/**
 * Vertical step-by-step progress indicator for a long-running AI pipeline
 * (X-ray structural analysis, gait functional analysis). The backend runs
 * these synchronously in one HTTP request with no incremental progress
 * events, so this advances on a timer tuned to roughly match real pipeline
 * timing and *holds* on the final step until the actual API response
 * arrives — it never claims "done" before the server really is.
 *
 * activeIndex: -1 = idle/hidden, 0..steps.length-1 = which step is active
 * (all before it are done), steps.length = everything complete.
 */
export default function ProcessFlow({ steps, activeIndex, accent = 'gold' }) {
  if (activeIndex < 0) return null

  const accentBg = accent === 'amethyst' ? 'bg-amethyst' : 'bg-gold'
  const accentText = accent === 'amethyst' ? 'text-white' : 'text-ink'

  return (
    <div className="bg-card-alt rounded-lg p-4 animate-fade-in">
      {steps.map((step, i) => {
        const Icon = step.icon
        const isDone = activeIndex > i || activeIndex >= steps.length
        const isActive = activeIndex === i
        const isLast = i === steps.length - 1

        return (
          <div key={step.label} className="flex gap-3">
            <div className="flex flex-col items-center">
              <div
                className={`w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 transition-colors duration-300 ${
                  isDone
                    ? 'bg-malachite text-white'
                    : isActive
                      ? `${accentBg} ${accentText} animate-pulse`
                      : 'bg-white border border-border text-faint'
                }`}
              >
                {isDone ? <IconCheck size={14} /> : <Icon size={14} />}
              </div>
              {!isLast && (
                <div className={`w-px flex-1 min-h-[16px] transition-colors duration-300 ${isDone ? 'bg-malachite' : 'bg-border'}`} />
              )}
            </div>
            <div className={`pb-4 pt-1 text-[12px] leading-tight ${isActive ? 'text-body font-semibold' : isDone ? 'text-body' : 'text-faint'}`}>
              {step.label}
              {isActive && <span className="inline-block ml-0.5 animate-pulse">…</span>}
            </div>
          </div>
        )
      })}
    </div>
  )
}
