import type { ReactNode } from 'react'

interface StatCardProps {
  label: string
  value: number | string
  icon: ReactNode
  trend?: string
  accent?: 'indigo' | 'emerald' | 'amber' | 'violet'
}

const ACCENT: Record<NonNullable<StatCardProps['accent']>, string> = {
  indigo: 'from-indigo-500/20 to-indigo-600/5 text-indigo-300',
  emerald: 'from-emerald-500/20 to-emerald-600/5 text-emerald-300',
  amber: 'from-amber-500/20 to-amber-600/5 text-amber-300',
  violet: 'from-violet-500/20 to-violet-600/5 text-violet-300',
}

export function StatCard({
  label,
  value,
  icon,
  trend,
  accent = 'indigo',
}: StatCardProps) {
  return (
    <div className="surface-card-hover group relative overflow-hidden p-4 sm:p-5">
      <div
        className={`absolute -right-4 -top-4 flex h-20 w-20 items-center justify-center rounded-full bg-gradient-to-br opacity-60 transition-transform duration-300 group-hover:scale-110 ${ACCENT[accent]}`}
      >
        <span className="text-2xl opacity-80">{icon}</span>
      </div>
      <p className="text-xs font-medium uppercase tracking-wider text-slate-500 sm:text-sm">
        {label}
      </p>
      <p className="mt-2 text-2xl font-bold tabular-nums text-white sm:text-3xl">{value}</p>
      {trend ? <p className="mt-1 text-xs text-slate-500">{trend}</p> : null}
    </div>
  )
}
