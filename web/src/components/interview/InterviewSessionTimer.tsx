import { useEffect, useState } from 'react'

interface InterviewSessionTimerProps {
  durationMinutes: number
  startedAt: string | null
}

export function InterviewSessionTimer({
  durationMinutes,
  startedAt,
}: InterviewSessionTimerProps) {
  const [elapsed, setElapsed] = useState(0)

  useEffect(() => {
    const startMs = startedAt ? new Date(startedAt).getTime() : Date.now()
    const tick = () => setElapsed(Math.floor((Date.now() - startMs) / 1000))
    tick()
    const id = window.setInterval(tick, 1000)
    return () => window.clearInterval(id)
  }, [startedAt])

  const totalSec = durationMinutes * 60
  const remaining = Math.max(0, totalSec - elapsed)
  const mins = Math.floor(remaining / 60)
  const secs = remaining % 60
  const pct = totalSec ? Math.min(100, (elapsed / totalSec) * 100) : 0

  return (
    <div className="surface-card px-4 py-3 sm:px-5">
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-wider text-slate-500">Session timer</p>
          <p className="text-xl font-semibold tabular-nums text-white">
            {String(mins).padStart(2, '0')}:{String(secs).padStart(2, '0')}
          </p>
        </div>
        <p className="text-xs text-slate-400">{durationMinutes} min allotted</p>
      </div>
      <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-white/10">
        <div
          className="h-full rounded-full bg-gradient-to-r from-indigo-500 to-violet-500 transition-all"
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  )
}
