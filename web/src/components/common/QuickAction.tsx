import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'

interface QuickActionProps {
  to: string
  title: string
  description: string
  icon: ReactNode
}

export function QuickAction({ to, title, description, icon }: QuickActionProps) {
  return (
    <Link
      to={to}
      className="surface-card-hover group flex items-start gap-4 p-4 sm:p-5"
    >
      <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-indigo-500/15 text-lg text-indigo-300 transition-colors group-hover:bg-indigo-500/25">
        {icon}
      </div>
      <div className="min-w-0">
        <p className="font-medium text-white">{title}</p>
        <p className="mt-0.5 text-sm text-slate-400">{description}</p>
      </div>
    </Link>
  )
}
