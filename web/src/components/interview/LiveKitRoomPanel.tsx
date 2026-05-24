import '@livekit/components-styles'

import {
  LiveKitRoom,
  ParticipantTile,
  RoomAudioRenderer,
  useRemoteParticipants,
  useTracks,
} from '@livekit/components-react'
import { Track } from 'livekit-client'
import { Alert, Button, Spin } from 'antd'
import { useMemo, useState } from 'react'

import { AiInterviewerPanel } from '@/components/interview/AiInterviewerPanel'
import { isAgentParticipant } from '@/components/interview/agentParticipant'
import type { TranscriptEntry } from '@/features/interviews/interviewsSlice'
import type { LiveKitTokenResponse } from '@/types/api'

interface LiveKitRoomPanelProps {
  credentials: LiveKitTokenResponse
  transcript: TranscriptEntry[]
  onDisconnect?: () => void
}

function InterviewRoomLayout({
  transcript,
  onLeave,
}: {
  transcript: TranscriptEntry[]
  onLeave?: () => void
}) {
  const cameraTracks = useTracks([{ source: Track.Source.Camera, withPlaceholder: true }])
  const localCamera = cameraTracks.find((track) => track.participant.isLocal)
  const remoteParticipants = useRemoteParticipants()

  const videoTracks = useTracks([
    { source: Track.Source.Camera, withPlaceholder: false },
    { source: Track.Source.Unknown, withPlaceholder: false },
  ])

  const agentVideoTrack = useMemo(
    () =>
      videoTracks.find(
        (track) =>
          !track.participant.isLocal &&
          track.publication &&
          isAgentParticipant(track.participant.identity, track.participant.name),
      ),
    [videoTracks],
  )

  const agentOnline = remoteParticipants.some((p) =>
    isAgentParticipant(p.identity, p.name),
  )

  return (
    <div className="grid h-full min-h-[320px] grid-cols-1 md:grid-cols-2">
      <div className="relative flex min-h-[240px] flex-col border-b border-white/10 bg-slate-900/50 md:border-b-0 md:border-r">
        <div className="absolute left-3 top-3 z-10 rounded-full bg-black/50 px-2.5 py-1 text-[10px] font-medium uppercase tracking-wider text-white">
          You
        </div>
        {localCamera ? (
          <ParticipantTile
            trackRef={localCamera}
            className="!h-full !min-h-[240px] !w-full"
          />
        ) : (
          <div className="flex flex-1 items-center justify-center text-slate-500">
            Camera starting…
          </div>
        )}
      </div>

      <AiInterviewerPanel
        connected
        agentOnline={agentOnline}
        transcript={transcript}
        agentVideoTrack={agentVideoTrack}
      />

      <div className="col-span-full flex justify-end border-t border-white/10 px-4 py-2">
        <Button size="small" danger onClick={onLeave}>
          Leave room
        </Button>
      </div>
    </div>
  )
}

export function LiveKitRoomPanel({
  credentials,
  transcript,
  onDisconnect,
}: LiveKitRoomPanelProps) {
  const [connected, setConnected] = useState(false)
  const [connectError, setConnectError] = useState<string | null>(null)

  return (
    <section className="surface-card overflow-hidden">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-white/[0.06] px-4 py-3 sm:px-5">
        <div className="min-w-0">
          <p className="text-sm font-medium text-white sm:text-base">
            Live interview · you &amp; Alex
          </p>
          <p className="truncate text-xs text-slate-400">{credentials.room}</p>
        </div>
      </div>

      {connectError ? (
        <Alert type="error" message={connectError} showIcon className="m-4" />
      ) : null}

      <div className="relative min-h-[320px] bg-slate-950/90 sm:min-h-[400px]">
        {!connected ? (
          <div className="absolute inset-0 z-10 flex items-center justify-center bg-slate-950/60">
            <Spin tip="Connecting to LiveKit…" size="large" />
          </div>
        ) : null}

        <LiveKitRoom
          serverUrl={credentials.url}
          token={credentials.token}
          connect
          audio
          video
          onConnected={() => {
            setConnected(true)
            setConnectError(null)
          }}
          onDisconnected={() => {
            setConnected(false)
            onDisconnect?.()
          }}
          onError={(error) => setConnectError(error.message)}
          className="h-full min-h-[320px] w-full"
        >
          {connected ? (
            <InterviewRoomLayout transcript={transcript} onLeave={onDisconnect} />
          ) : null}
          <RoomAudioRenderer />
        </LiveKitRoom>
      </div>
    </section>
  )
}
