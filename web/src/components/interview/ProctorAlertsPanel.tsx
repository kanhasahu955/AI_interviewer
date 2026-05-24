import { Alert, List, Typography } from 'antd'
import startCase from 'lodash/startCase'

import type { ProctorEntry } from '@/features/interviews/interviewsSlice'

interface ProctorAlertsPanelProps {
  events: ProctorEntry[]
}

const SEVERITY_COLOR: Record<string, string> = {
  info: 'text-slate-400',
  warn: 'text-amber-300',
  critical: 'text-red-300',
}

export function ProctorAlertsPanel({ events }: ProctorAlertsPanelProps) {
  return (
    <section className="surface-card flex max-h-[320px] min-h-[200px] flex-col overflow-hidden">
      <div className="border-b border-white/[0.06] px-4 py-3 sm:px-5">
        <Typography.Text className="!font-medium !text-white">
          Proctoring alerts
        </Typography.Text>
        <p className="mt-0.5 text-xs text-slate-500">
          Tab switches, network drops, and AI vision checks
        </p>
      </div>

      {events.length === 0 ? (
        <div className="flex flex-1 items-center justify-center p-4">
          <Alert
            type="info"
            showIcon
            message="Monitoring active"
            description="No alerts yet. Stay in frame and keep this tab focused."
            className="!w-full"
          />
        </div>
      ) : (
        <List
          className="flex-1 overflow-y-auto px-2 py-2"
          dataSource={[...events].reverse().slice(0, 30)}
          renderItem={(item) => (
            <List.Item className="!border-none !px-2 !py-1.5">
              <div className="w-full rounded-lg bg-white/[0.04] px-3 py-2">
                <div className="flex items-center justify-between gap-2">
                  <span className="text-xs font-medium text-indigo-300">
                    {startCase(item.kind.replace(/_/g, ' '))}
                  </span>
                  <span
                    className={`text-[10px] uppercase ${SEVERITY_COLOR[item.severity] ?? 'text-slate-400'}`}
                  >
                    {item.severity}
                  </span>
                </div>
              </div>
            </List.Item>
          )}
        />
      )}
    </section>
  )
}
