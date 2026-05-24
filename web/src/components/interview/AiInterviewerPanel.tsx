import { ParticipantTile } from '@livekit/components-react'
import type { TrackReferenceOrPlaceholder } from '@livekit/components-core'
import { useMemo } from 'react'

import { InterviewerVideoTile } from '@/components/interview/LivePortraitAvatar'
import { useAgentAudioLevel } from '@/hooks/useAgentAudioLevel'
import type { TranscriptEntry } from '@/features/interviews/interviewsSlice'

export type InterviewerStatus =
  | 'offline'
  | 'connecting'
  | 'waiting'
  | 'speaking'
  | 'listening'

interface AiInterviewerPanelProps {
  connected: boolean
  agentOnline: boolean
  transcript: TranscriptEntry[]
  agentVideoTrack?: TrackReferenceOrPlaceholder
  name?: string
  title?: string
}

function deriveStatus(
  connected: boolean,
  agentOnline: boolean,
  transcript: TranscriptEntry[],
  agentSpeaking: boolean,
): InterviewerStatus {
  if (!connected) return 'offline'
  if (!agentOnline && transcript.length === 0) return 'connecting'
  if (agentSpeaking) return 'speaking'

  const last = transcript[transcript.length - 1]
  if (!last) return agentOnline ? 'waiting' : 'connecting'

  const ageMs = Date.now() - last.ts
  if (last.role === 'assistant' && ageMs < 12000) return 'speaking'
  if (last.role === 'user' && ageMs < 15000) return 'listening'
  return agentOnline ? 'waiting' : 'connecting'
}

const STATUS_COPY: Record<InterviewerStatus, string> = {
  offline: 'Offline',
  connecting: 'Joining…',
  waiting: 'In session',
  speaking: 'Speaking',
  listening: 'Listening',
}

const INTERVIEWER_PHOTO = '/avatars/alex.jpg'

export function AiInterviewerPanel({
  connected,
  agentOnline,
  transcript,
  agentVideoTrack,
  name = 'Alex',
  title = 'Senior Technical Interviewer',
}: AiInterviewerPanelProps) {
  const voice = useAgentAudioLevel(connected && agentOnline)

  const lastAssistant = useMemo(
    () => [...transcript].reverse().find((e) => e.role === 'assistant'),
    [transcript],
  )

  const hasLiveVideo =
    agentVideoTrack &&
    !agentVideoTrack.participant.isLocal &&
    agentVideoTrack.publication

  const status = deriveStatus(
    connected,
    agentOnline,
    transcript,
    voice.isSpeaking,
  )
  const isSpeaking = status === 'speaking' || voice.isSpeaking
  const isLive = connected && (agentOnline || transcript.length > 0)

  return (
    <div className="relative flex min-h-[240px] flex-col bg-slate-900">
      <div className="absolute left-3 top-3 z-10 flex items-center gap-2">
        <span className="rounded-full bg-black/55 px-2.5 py-1 text-[10px] font-medium uppercase tracking-wider text-white backdrop-blur-sm">
          {name} · Interviewer
        </span>
        {isLive ? (
          <span className="flex items-center gap-1 rounded-full bg-red-600/90 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide text-white">
            <span className="inline-block h-1.5 w-1.5 animate-pulse rounded-full bg-white" />
            Live
          </span>
        ) : null}
      </div>

      <div className="absolute right-3 top-3 z-10 rounded-full bg-black/55 px-2.5 py-1 text-[10px] font-medium text-white/90 backdrop-blur-sm">
        {STATUS_COPY[status]}
      </div>

      {hasLiveVideo ? (
        <ParticipantTile
          trackRef={agentVideoTrack}
          className="!h-full !min-h-[240px] !w-full [&_.lk-participant-metadata]:hidden"
        />
      ) : (
        <InterviewerVideoTile
          name={name}
          stillSrc={INTERVIEWER_PHOTO}
          portraitVideoUrl={lastAssistant?.portraitUrl}
          isSpeaking={isSpeaking}
          audioLevel={voice.level}
        />
      )}

      {lastAssistant ? (
        <div className="absolute bottom-0 left-0 right-0 z-10 border-t border-white/10 bg-gradient-to-t from-black/80 via-black/60 to-transparent px-4 pb-3 pt-8">
          <p className="text-[10px] font-medium uppercase tracking-wider text-white/50">
            {title}
          </p>
          <p className="mt-0.5 line-clamp-2 text-sm leading-snug text-white/95">
            {lastAssistant.content}
          </p>
        </div>
      ) : connected && !agentOnline ? (
        <div className="absolute bottom-3 left-3 right-3 z-10 rounded-lg bg-amber-950/80 px-3 py-2 text-center text-xs text-amber-100/90 backdrop-blur-sm">
          Connecting interviewer…
        </div>
      ) : null}
    </div>
  )
}
