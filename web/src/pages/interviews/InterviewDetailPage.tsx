import {
  Alert,
  Button,
  Descriptions,
  List,
  Space,
  Typography,
} from 'antd'
import { PlayCircleOutlined } from '@ant-design/icons'
import { Suspense, lazy, useEffect } from 'react'
import { Link, useParams } from 'react-router-dom'

import { useAppDispatch, useAppSelector } from '@/app/hooks'
import { LoadingScreen } from '@/components/common/LoadingScreen'
import { PageContainer } from '@/components/common/PageContainer'
import { PageHeader } from '@/components/common/PageHeader'
import { SectionCard } from '@/components/common/SectionCard'
import { StatusBadge } from '@/components/common/StatusBadge'
import { LiveTranscriptPanel } from '@/components/interview/LiveTranscriptPanel'
import { useInterviewWebSocket } from '@/hooks/useInterviewWebSocket'
import { interviewsActions } from '@/features/interviews/interviewsSlice'
import { reportsActions } from '@/features/reports/reportsSlice'
import type { TurnPublic } from '@/types/api'

const LiveKitRoomPanel = lazy(async () => {
  const module = await import('@/components/interview/LiveKitRoomPanel')
  return { default: module.LiveKitRoomPanel }
})

export function InterviewDetailPage() {
  const { id } = useParams()
  const interviewId = Number(id)
  const dispatch = useAppDispatch()
  const role = useAppSelector((state) => state.auth.user?.role)
  const {
    selected,
    turns,
    transcript,
    wsStatus,
    liveKit,
    detailLoading,
    actionLoading,
    error,
  } = useAppSelector((state) => state.interviews)
  const report = useAppSelector((state) => state.reports.current)

  const canJoin =
    (role === 'candidate' || role === 'admin') &&
    selected?.status !== 'completed' &&
    selected?.status !== 'cancelled'

  useInterviewWebSocket(Number.isFinite(interviewId) ? interviewId : null)

  useEffect(() => {
    if (!Number.isFinite(interviewId)) return
    dispatch(interviewsActions.fetchInterviewRequest(interviewId))
  }, [dispatch, interviewId])

  useEffect(() => {
    if (selected?.status === 'completed') {
      dispatch(reportsActions.fetchReportRequest(interviewId))
    }
  }, [dispatch, interviewId, selected?.status])

  useEffect(() => {
    return () => {
      dispatch(interviewsActions.clearLiveKit())
    }
  }, [dispatch])

  const handleLeaveRoom = () => {
    dispatch(interviewsActions.clearLiveKit())
  }

  const handleEnd = () => {
    dispatch(interviewsActions.endInterviewRequest(interviewId))
    dispatch(reportsActions.fetchReportRequest(interviewId))
    dispatch(interviewsActions.clearLiveKit())
  }

  if (detailLoading && !selected) {
    return <LoadingScreen label="Loading interview…" fullPage />
  }

  if (!selected) {
    return (
      <PageContainer>
        <Alert type="error" message={error ?? 'Interview not found'} showIcon />
      </PageContainer>
    )
  }

  return (
    <PageContainer>
      <PageHeader
        title={`Interview #${selected.id}`}
        subtitle="Join the live room, follow the transcript, and review Q&A turns."
        extra={
          <Space wrap className="w-full sm:w-auto">
            <StatusBadge status={selected.status} />
            {canJoin && !liveKit ? (
              <Link to={`/interviews/${selected.id}/room`}>
                <Button type="primary" icon={<PlayCircleOutlined />} block className="sm:!w-auto">
                  Enter interview room
                </Button>
              </Link>
            ) : null}
            {selected.status !== 'completed' ? (
              <Button danger loading={actionLoading} onClick={handleEnd} block className="sm:!w-auto">
                End interview
              </Button>
            ) : (
              <Link to={`/reports/${selected.id}`}>
                <Button block className="sm:!w-auto">View report</Button>
              </Link>
            )}
          </Space>
        }
      />

      {error ? <Alert type="error" message={error} showIcon className="mb-4" /> : null}

      {liveKit ? (
        <div className="mb-6">
          <Suspense fallback={<LoadingScreen label="Loading video room…" />}>
            <LiveKitRoomPanel
              credentials={liveKit}
              transcript={transcript}
              onDisconnect={handleLeaveRoom}
            />
          </Suspense>
        </div>
      ) : null}

      <div className="mb-6 grid gap-4 lg:grid-cols-2 lg:gap-6">
        <SectionCard title="Overview">
          <Descriptions column={{ xs: 1, sm: 2 }} size="small" className="!text-slate-300">
            <Descriptions.Item label="Status">
              <StatusBadge status={selected.status} />
            </Descriptions.Item>
            <Descriptions.Item label="Duration">
              {selected.duration_minutes} min
            </Descriptions.Item>
            <Descriptions.Item label="JD">#{selected.jd_id}</Descriptions.Item>
            <Descriptions.Item label="Candidate">#{selected.candidate_id}</Descriptions.Item>
            <Descriptions.Item label="Room" span={2}>
              <span className="break-all text-slate-400">
                {selected.livekit_room ?? '—'}
              </span>
            </Descriptions.Item>
          </Descriptions>
        </SectionCard>

        <LiveTranscriptPanel entries={transcript} wsStatus={wsStatus} />
      </div>

      <SectionCard title="Turn history" className="mb-6">
        <List
          locale={{ emptyText: 'No turns recorded yet' }}
          dataSource={turns}
          renderItem={(turn: TurnPublic) => (
            <List.Item className="!border-white/[0.04] !px-0">
              <div className="w-full rounded-xl bg-white/[0.03] p-3 sm:p-4">
                <Typography.Text className="!text-xs !uppercase !tracking-wider !text-indigo-300">
                  {turn.skill_tag ?? `Turn ${turn.idx + 1}`}
                </Typography.Text>
                <Typography.Paragraph className="!mb-2 !mt-2 !font-medium !text-white">
                  {turn.question}
                </Typography.Paragraph>
                <Typography.Paragraph className="!mb-0 !text-sm !text-slate-400">
                  {turn.answer_text ?? 'No answer recorded'}
                </Typography.Paragraph>
              </div>
            </List.Item>
          )}
        />
      </SectionCard>

      {report ? (
        <SectionCard title="Report preview">
          <Typography.Paragraph className="!text-slate-300">
            {report.summary}
          </Typography.Paragraph>
          <div className="flex flex-wrap gap-3 text-sm">
            <span className="rounded-full bg-indigo-500/15 px-3 py-1 text-indigo-300">
              Score: {report.overall_score}
            </span>
            <span className="rounded-full bg-white/5 px-3 py-1 text-slate-400">
              {report.recommendation}
            </span>
          </div>
        </SectionCard>
      ) : null}
    </PageContainer>
  )
}
