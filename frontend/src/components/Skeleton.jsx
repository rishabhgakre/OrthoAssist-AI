export function Skeleton({ className = '' }) {
  return (
    <div
      className={`rounded-md bg-[linear-gradient(90deg,theme(colors.card-alt)_25%,#efe9d8_37%,theme(colors.card-alt)_63%)] bg-[length:400%_100%] animate-shimmer ${className}`}
    />
  )
}

export function SkeletonStatCards({ count = 4 }) {
  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="bg-card border border-border rounded-xl px-4 py-4">
          <Skeleton className="h-3 w-20 mb-3" />
          <Skeleton className="h-6 w-14" />
        </div>
      ))}
    </div>
  )
}

export function SkeletonRows({ count = 5 }) {
  return (
    <div className="bg-card border border-border rounded-xl overflow-hidden divide-y divide-border">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="flex items-center gap-3 px-4 py-3.5">
          <Skeleton className="w-8 h-8 rounded-full flex-shrink-0" />
          <div className="flex-1">
            <Skeleton className="h-3 w-32 mb-2" />
            <Skeleton className="h-2.5 w-20" />
          </div>
        </div>
      ))}
    </div>
  )
}
