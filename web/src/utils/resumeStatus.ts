import type { ResumePublic } from '@/types/api'

export type ResumeStatus = 'indexed' | 'uploaded' | 'pending'

function isTextReady(resume: ResumePublic): boolean {
  const parsed = resume.parsed
  if (!parsed) return true
  return parsed.text_ready !== false
}

export function getResumeStatus(resume: ResumePublic): ResumeStatus {
  if (resume.ingested) return 'indexed'
  if (!isTextReady(resume)) return 'pending'
  return 'uploaded'
}

export function getResumeStatusLabel(resume: ResumePublic): string {
  switch (getResumeStatus(resume)) {
    case 'indexed':
      return 'Indexed for AI'
    case 'uploaded':
      return 'Ready'
    default:
      return 'Parse failed'
  }
}

export function getResumeStatusBadgeClass(resume: ResumePublic): string {
  switch (getResumeStatus(resume)) {
    case 'indexed':
      return 'bg-emerald-500/15 text-emerald-300'
    case 'uploaded':
      return 'bg-indigo-500/15 text-indigo-300'
    default:
      return 'bg-amber-500/15 text-amber-300'
  }
}
