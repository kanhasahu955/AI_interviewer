import {
  CheckCircleOutlined,
  CloseCircleOutlined,
  LoadingOutlined,
  MinusCircleOutlined,
} from '@ant-design/icons'
import { Progress, Typography } from 'antd'
import { useEffect, useRef } from 'react'

import type { ResumeAnalysisEvent } from '@/types/api'

interface ResumeAnalysisTimelineProps {
  events: ResumeAnalysisEvent[]
  active: boolean
  progress: number
}

const STEP_LABELS: Record<string, string> = {
  started: 'Initialize',
  load_document: 'Read document',
  sanitize: 'Normalize text',
  extract_skills: 'Extract skills',
  extract_sections: 'Detect sections',
  extract_contact: 'Contact hints',
  save: 'Persist results',
  complete: 'Complete',
}

function statusIcon(status: ResumeAnalysisEvent['status']) {
  if (status === 'done') {
    return <CheckCircleOutlined className="text-emerald-400" />
  }
  if (status === 'error') {
    return <CloseCircleOutlined className="text-red-400" />
  }
  if (status === 'running') {
    return <LoadingOutlined spin className="text-indigo-400" />
  }
  return <MinusCircleOutlined className="text-slate-600" />
}

export function ResumeAnalysisTimeline({
  events,
  active,
  progress,
}: ResumeAnalysisTimelineProps) {
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    scrollRef.current?.scrollTo({
      top: scrollRef.current.scrollHeight,
      behavior: 'smooth',
    })
  }, [events.length])

  const stageEvents = events.filter((e) => e.type === 'stage' || e.type === 'log' || e.type === 'error')

  return (
    <div className="rounded-xl border border-white/[0.08] bg-black/30">
      <div className="border-b border-white/[0.06] px-4 py-3">
        <div className="flex items-center justify-between gap-3">
          <Typography.Text className="!font-medium !text-white">
            Analysis activity
          </Typography.Text>
          <Typography.Text className="!text-xs !text-slate-500">
            {active ? 'Live stream' : 'Finished'}
          </Typography.Text>
        </div>
        <Progress
          percent={progress}
          size="small"
          showInfo={false}
          strokeColor={{ from: '#6366f1', to: '#8b5cf6' }}
          className="!mt-2"
        />
      </div>

      <div
        ref={scrollRef}
        className="max-h-[280px] overflow-y-auto px-3 py-3 font-mono text-xs"
      >
        {stageEvents.length === 0 ? (
          <p className="px-2 py-4 text-center text-slate-500">
            Waiting for analysis events…
          </p>
        ) : (
          <ul className="space-y-2">
            {stageEvents.map((event, idx) => (
              <li
                key={`${event.step}-${event.ts ?? idx}-${event.message}`}
                className="flex gap-2.5 rounded-lg bg-white/[0.03] px-3 py-2"
              >
                <span className="mt-0.5 shrink-0">{statusIcon(event.status)}</span>
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="font-medium text-indigo-300">
                      {STEP_LABELS[event.step] ?? event.step}
                    </span>
                    {event.ts ? (
                      <span className="text-[10px] text-slate-600">
                        {new Date(event.ts).toLocaleTimeString()}
                      </span>
                    ) : null}
                  </div>
                  <p className="mt-0.5 break-words text-slate-400">{event.message}</p>
                  {event.detail && Object.keys(event.detail).length > 0 && event.type === 'log' ? (
                    <pre className="mt-1.5 max-h-20 overflow-auto whitespace-pre-wrap text-[10px] text-slate-500">
                      {JSON.stringify(event.detail, null, 2)}
                    </pre>
                  ) : null}
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}
