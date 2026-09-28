export default function EmptyState({ icon: Icon, title, sub, action }) {
  return (
    <div className="text-center py-14 px-4">
      {Icon && (
        <div className="w-12 h-12 rounded-xl bg-card-alt flex items-center justify-center mx-auto mb-4 text-muted">
          <Icon size={20} stroke={1.6} />
        </div>
      )}
      <div className="text-[13.5px] font-medium text-body mb-1">{title}</div>
      {sub && <div className="text-[12px] text-muted max-w-xs mx-auto leading-relaxed">{sub}</div>}
      {action && <div className="mt-4">{action}</div>}
    </div>
  )
}
