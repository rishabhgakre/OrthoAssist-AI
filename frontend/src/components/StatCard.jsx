export default function StatCard({ label, value, icon: Icon, valueClassName = 'text-body', sub }) {
  return (
    <div className="bg-card border border-border rounded-xl px-4 py-4 flex items-start gap-3 hover:shadow-card-hover transition-shadow">
      {Icon && (
        <div className="w-9 h-9 rounded-lg bg-ink flex items-center justify-center flex-shrink-0 text-gold">
          <Icon size={17} stroke={1.8} />
        </div>
      )}
      <div className="min-w-0">
        <div className="text-[10px] tracking-wide text-muted font-mono uppercase mb-1.5">{label}</div>
        <div className={`font-mono text-[22px] leading-none font-medium ${valueClassName}`}>{value}</div>
        {sub && <div className="text-[10.5px] text-faint mt-1.5">{sub}</div>}
      </div>
    </div>
  )
}
