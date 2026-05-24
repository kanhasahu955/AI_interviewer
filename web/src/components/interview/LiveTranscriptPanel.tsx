import { Badge, List, Typography } from 'antd'
import startCase from 'lodash/startCase'

import type { TranscriptEntry } from '@/features/interviews/interviewsSlice'
import type { WebSocketStatus } from '@/core/websocket/WebSocketClient'

interface LiveTranscriptPanelProps {
  entries: TranscriptEntry[]
  wsStatus: WebSocketStatus
}

const STATUS_LABEL: Record<WebSocketStatus, string> = {
  idle: 'Idle',
  connecting: 'Connecting…',
  open: 'Live',
  closed: 'Disconnected',
  error: 'Error',
}

export function LiveTranscriptPanel({
  entries,
  wsStatus,
}: LiveTranscriptPanelProps) {
  return (
    <section className="surface-card flex h-[min(420px,55vh)] min-h-[280px] flex-col overflow-hidden sm:min-h-[320px]">
      <div className="flex shrink-0 items-center justify-between gap-2 border-b border-white/[0.06] px-4 py-3 sm:px-5">
        <Typography.Text className="!font-medium !text-white">
          Live transcript
        </Typography.Text>
        <Badge
          status={wsStatus === 'open' ? 'processing' : 'default'}
          text={
            <span className="text-xs text-slate-400 sm:text-sm">
              {STATUS_LABEL[wsStatus]}
            </span>
          }
        />
      </div>
      <List
        className="flex-1 overflow-y-auto px-2 py-2 sm:px-3"
        locale={{ emptyText: 'Waiting for live updates…' }}
        dataSource={entries}
        renderItem={(item) => (
          <List.Item className="!border-none !px-1 !py-1.5 sm:!px-2">
            <div className="w-full rounded-xl bg-white/[0.04] px-3 py-2.5 sm:px-4">
              <Typography.Text className="!text-[10px] !uppercase !tracking-wider !text-indigo-300 sm:!text-xs">
                {startCase(item.role)}
              </Typography.Text>
              <Typography.Paragraph className="!mb-0 !mt-1 !text-sm !leading-relaxed !text-slate-200 sm:!text-base">
                {item.content}
              </Typography.Paragraph>
            </div>
          </List.Item>
        )}
      />
    </section>
  )
}
