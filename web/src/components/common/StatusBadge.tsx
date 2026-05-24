import { Tag } from 'antd'
import startCase from 'lodash/startCase'

import type { InterviewStatus } from '@/types/api'

const STATUS_STYLES: Record<InterviewStatus, { color: string; bg: string }> = {
  scheduled: { color: '#93c5fd', bg: 'rgba(59,130,246,0.15)' },
  live: { color: '#6ee7b7', bg: 'rgba(16,185,129,0.15)' },
  completed: { color: '#cbd5e1', bg: 'rgba(148,163,184,0.12)' },
  cancelled: { color: '#fca5a5', bg: 'rgba(248,113,113,0.12)' },
  flagged: { color: '#fcd34d', bg: 'rgba(251,191,36,0.15)' },
}

interface StatusBadgeProps {
  status: InterviewStatus | string
}

export function StatusBadge({ status }: StatusBadgeProps) {
  const style = STATUS_STYLES[status as InterviewStatus] ?? STATUS_STYLES.completed

  return (
    <Tag
      bordered={false}
      className="!m-0 !rounded-full !px-2.5 !py-0.5 !text-xs !font-medium"
      style={{ color: style.color, background: style.bg }}
    >
      {startCase(status)}
    </Tag>
  )
}
