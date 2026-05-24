import {
  CalendarOutlined,
  ClockCircleOutlined,
  FileTextOutlined,
  PlayCircleOutlined,
} from '@ant-design/icons'
import { Button } from 'antd'
import dayjs from 'dayjs'
import { Link } from 'react-router-dom'

import { useAppSelector } from '@/app/hooks'
import { StatusBadge } from '@/components/common/StatusBadge'
import type { InterviewPublic } from '@/types/api'

interface InterviewCardProps {
  interview: InterviewPublic
}

export function InterviewCard({ interview }: InterviewCardProps) {
  const role = useAppSelector((state) => state.auth.user?.role)
  const canEnterRoom =
    (role === 'candidate' || role === 'admin') &&
    (interview.status === 'scheduled' || interview.status === 'live')

  return (
    <article className="surface-card-hover group flex h-full flex-col p-4 sm:p-5">
      <Link to={`/interviews/${interview.id}`} className="flex flex-1 flex-col">
        <div className="mb-4 flex items-start justify-between gap-3">
          <div className="min-w-0">
            <p className="text-xs font-medium uppercase tracking-wider text-indigo-400/80">
              Interview
            </p>
            <h3 className="truncate text-lg font-semibold text-white">
              Session #{interview.id}
            </h3>
          </div>
          <StatusBadge status={interview.status} />
        </div>

        <ul className="mt-auto space-y-2.5 text-sm text-slate-400">
          <li className="flex items-center gap-2.5">
            <FileTextOutlined className="shrink-0 text-slate-500" />
            <span className="truncate">JD #{interview.jd_id}</span>
          </li>
          <li className="flex items-center gap-2.5">
            <ClockCircleOutlined className="shrink-0 text-slate-500" />
            <span>{interview.duration_minutes} min</span>
          </li>
          {interview.started_at ? (
            <li className="flex items-center gap-2.5">
              <CalendarOutlined className="shrink-0 text-slate-500" />
              <span>{dayjs(interview.started_at).format('MMM D, YYYY · HH:mm')}</span>
            </li>
          ) : (
            <li className="flex items-center gap-2.5 text-slate-500">
              <CalendarOutlined className="shrink-0" />
              <span>Not started yet</span>
            </li>
          )}
        </ul>
      </Link>

      <div className="mt-4 flex flex-wrap gap-2 border-t border-white/[0.06] pt-3">
        {canEnterRoom ? (
          <Link to={`/interviews/${interview.id}/room`} className="flex-1">
            <Button type="primary" icon={<PlayCircleOutlined />} block>
              {interview.status === 'live' ? 'Rejoin room' : 'Enter interview room'}
            </Button>
          </Link>
        ) : (
          <Link to={`/interviews/${interview.id}`} className="flex-1">
            <Button block>View details</Button>
          </Link>
        )}
      </div>
    </article>
  )
}
