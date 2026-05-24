import { Empty } from 'antd'
import type { ReactNode } from 'react'

interface EmptyStateProps {
  description?: string
  action?: ReactNode
}

export function EmptyState({
  description = 'Nothing here yet',
  action,
}: EmptyStateProps) {
  return (
    <div className="surface-card flex min-h-[220px] flex-col items-center justify-center p-8 sm:min-h-[280px] sm:p-12">
      <Empty
        description={<span className="text-slate-400">{description}</span>}
      />
      {action ? <div className="mt-4">{action}</div> : null}
    </div>
  )
}
