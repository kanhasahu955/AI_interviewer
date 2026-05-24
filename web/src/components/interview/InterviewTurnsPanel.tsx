import { Typography } from 'antd'

import type { TurnPublic } from '@/types/api'

interface InterviewTurnsPanelProps {
  turns: TurnPublic[]
}

export function InterviewTurnsPanel({ turns }: InterviewTurnsPanelProps) {
  return (
    <section className="surface-card flex max-h-[320px] min-h-[200px] flex-col overflow-hidden">
      <div className="border-b border-white/[0.06] px-4 py-3 sm:px-5">
        <Typography.Text className="!font-medium !text-white">
          Saved Q&amp;A
        </Typography.Text>
        <p className="mt-0.5 text-xs text-slate-500">
          Questions and your answers stored in the database
        </p>
      </div>
      {turns.length === 0 ? (
        <div className="flex flex-1 items-center justify-center p-4 text-sm text-slate-500">
          Answers appear here as you respond to each question
        </div>
      ) : (
        <ul className="flex-1 space-y-2 overflow-y-auto px-3 py-3">
          {turns.map((turn) => (
            <li key={turn.idx} className="rounded-xl bg-white/[0.04] p-3">
              <p className="text-[10px] uppercase tracking-wider text-indigo-300">
                {turn.skill_tag ?? `Question ${turn.idx + 1}`}
              </p>
              <p className="mt-1 text-sm font-medium text-white">{turn.question}</p>
              <p className="mt-2 text-sm text-slate-400">
                {turn.answer_text ?? '—'}
              </p>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}
