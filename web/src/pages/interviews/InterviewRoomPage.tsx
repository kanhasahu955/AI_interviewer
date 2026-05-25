import { Alert, Button, Space } from 'antd'
import { Suspense, lazy, useEffect } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'

import { useAppDispatch, useAppSelector } from '@/app/hooks'
import { LoadingScreen } from '@/components/common/LoadingScreen'
import { PageContainer } from '@/components/common/PageContainer'
import { PageHeader } from '@/components/common/PageHeader'
import { StatusBadge } from '@/components/common/StatusBadge'
import { InterviewLobby } from '@/components/interview/InterviewLobby'
import { InterviewSessionTimer } from '@/components/interview/InterviewSessionTimer'
import { InterviewTurnsPanel } from '@/components/interview/InterviewTurnsPanel'
import { LiveTranscriptPanel } from '@/components/interview/LiveTranscriptPanel'
import { ProctorAlertsPanel } from '@/components/interview/ProctorAlertsPanel'
import { useInterviewWebSocket } from '@/hooks/useInterviewWebSocket'
import { useProctoring } from '@/hooks/useProctoring'
import { interviewsActions } from '@/features/interviews/interviewsSlice'
import { interviewService } from '@/services/InterviewService'
import { proctoringService } from '@/services/ProctoringService'

const LiveKitRoomPanel = lazy(async () => {
  const module = await import('@/components/interview/LiveKitRoomPanel')
  return { default: module.LiveKitRoomPanel }
})

export function InterviewRoomPage() {
  const { id } = useParams()
  const interviewId = Number(id)
  const navigate = useNavigate()
  const dispatch = useAppDispatch()
  const role = useAppSelector((state) => state.auth.user?.role)
  const {
    selected,
    liveKit,
    transcript,
    proctorEvents,
    wsStatus,
    detailLoading,
    tokenLoading,
    actionLoading,
    error,
    turns,
  } = useAppSelector((state) => state.interviews)

  const isCandidate = role === 'candidate' || role === 'admin'
  const sessionActive = Boolean(liveKit)
  const isCompleted = selected?.status === 'completed'
  const canJoinLive =
    isCandidate && selected && !isCompleted && selected.status !== 'cancelled'

  useInterviewWebSocket(Number.isFinite(interviewId) ? interviewId : null)
  useProctoring(interviewId, sessionActive && isCandidate)

  useEffect(() => {
    if (!Number.isFinite(interviewId)) return
    dispatch(interviewsActions.fetchInterviewRequest(interviewId))
    proctoringService
      .listEvents(interviewId)
      .then((events) => dispatch(interviewsActions.setProctorEvents(events)))
      .catch(() => undefined)
  }, [dispatch, interviewId])

  useEffect(() => {
    if (!Number.isFinite(interviewId) || !sessionActive) return
    const refreshTurns = () => {
      interviewService
        .getTurns(interviewId)
        .then((rows) => dispatch(interviewsActions.fetchTurnsSuccess(rows)))
        .catch(() => undefined)
    }
    refreshTurns()
    const id = window.setInterval(refreshTurns, 8000)
    return () => window.clearInterval(id)
  }, [dispatch, interviewId, sessionActive])

  useEffect(() => {
    if (!Number.isFinite(interviewId) || !sessionActive) return
    const refreshProctor = () => {
      proctoringService
        .listEvents(interviewId)
        .then((events) => dispatch(interviewsActions.setProctorEvents(events)))
        .catch(() => undefined)
    }
    refreshProctor()
    const id = window.setInterval(refreshProctor, 6000)
    return () => window.clearInterval(id)
  }, [dispatch, interviewId, sessionActive])

  useEffect(() => {
    return () => {
      dispatch(interviewsActions.clearLiveKit())
    }
  }, [dispatch])

  const handleJoin = () => {
    dispatch(interviewsActions.fetchLiveKitTokenRequest(interviewId))
  }

  const handleEnd = () => {
    dispatch(interviewsActions.endInterviewRequest(interviewId))
    dispatch(interviewsActions.clearLiveKit())
    navigate(`/interviews/${interviewId}`)
  }

  if (detailLoading && !selected) {
    return <LoadingScreen label="Preparing interview room…" fullPage />
  }

  if (!selected) {
    return (
      <PageContainer>
        <Alert type="error" message={error ?? 'Interview not found'} showIcon />
      </PageContainer>
    )
  }

  if (isCompleted) {
    return (
      <PageContainer>
        <Alert
          type="success"
          showIcon
          message="Interview completed"
          description="This session has ended."
          action={
            <Link to={`/reports/${selected.id}`}>
              <Button type="primary">View report</Button>
            </Link>
          }
        />
      </PageContainer>
    )
  }

  return (
    <PageContainer>
      <PageHeader
        title={`Live interview #${selected.id}`}
        subtitle={
          canJoinLive
            ? 'AI-powered voice interview with real-time proctoring.'
            : 'Monitor live transcript and proctoring alerts.'
        }
        extra={
          <Space wrap>
            <StatusBadge status={selected.status} />
            {sessionActive && canJoinLive ? (
              <Button danger loading={actionLoading} onClick={handleEnd}>
                End interview
              </Button>
            ) : (
              <Link to={`/interviews/${selected.id}`}>
                <Button>Interview details</Button>
              </Link>
            )}
          </Space>
        }
      />

      {error ? <Alert type="error" message={error} showIcon className="mb-4" /> : null}

      {canJoinLive && !sessionActive ? (
        <InterviewLobby loading={tokenLoading} onJoin={handleJoin} />
      ) : null}

      {canJoinLive && sessionActive ? (
        <>
          <div className="mb-4">
            <InterviewSessionTimer
              durationMinutes={selected.duration_minutes}
              startedAt={selected.started_at}
            />
          </div>
          <div className="mb-6">
            <Suspense fallback={<LoadingScreen label="Loading video room…" />}>
              <LiveKitRoomPanel
                credentials={liveKit!}
                transcript={transcript}
                onDisconnect={() => dispatch(interviewsActions.clearLiveKit())}
              />
            </Suspense>
          </div>
        </>
      ) : null}

      {!canJoinLive ? (
        <Alert
          type="info"
          showIcon
          className="mb-4"
          message="Recruiter watch mode"
          description="Live video is candidate-only. Transcript and proctor alerts update in real time below."
        />
      ) : null}

      <div className="mb-6 grid gap-4 lg:grid-cols-2 lg:gap-6">
        <LiveTranscriptPanel entries={transcript} wsStatus={wsStatus} />
        <InterviewTurnsPanel turns={turns} />
      </div>

      <div className="grid gap-4 lg:grid-cols-1">
        <ProctorAlertsPanel events={proctorEvents} />
      </div>
    </PageContainer>
  )
}
