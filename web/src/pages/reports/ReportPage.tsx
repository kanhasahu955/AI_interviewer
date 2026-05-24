import { ReloadOutlined } from '@ant-design/icons'
import { Alert, Button, Progress, Typography } from 'antd'
import { useEffect } from 'react'
import { useParams } from 'react-router-dom'

import { useAppDispatch, useAppSelector } from '@/app/hooks'
import { LoadingScreen } from '@/components/common/LoadingScreen'
import { PageContainer } from '@/components/common/PageContainer'
import { PageHeader } from '@/components/common/PageHeader'
import { SectionCard } from '@/components/common/SectionCard'
import { reportsActions } from '@/features/reports/reportsSlice'

export function ReportPage() {
  const { id } = useParams()
  const interviewId = Number(id)
  const dispatch = useAppDispatch()
  const { current, loading, error } = useAppSelector((state) => state.reports)

  useEffect(() => {
    if (Number.isFinite(interviewId)) {
      dispatch(reportsActions.fetchReportRequest(interviewId))
    }
    return () => {
      dispatch(reportsActions.clearReport())
    }
  }, [dispatch, interviewId])

  if (loading) {
    return (
      <PageContainer>
        <LoadingScreen label="Loading report…" fullPage />
      </PageContainer>
    )
  }

  if (error || !current) {
    return (
      <PageContainer>
        <Alert
          type="warning"
          showIcon
          message={error ?? 'Report not available'}
          description="Reports appear after an interview is completed and the report job finishes."
        />
      </PageContainer>
    )
  }

  const score = Math.round(current.overall_score)

  return (
    <PageContainer>
      <PageHeader
        title={`Interview #${current.interview_id} Report`}
        subtitle="AI-generated evaluation, strengths, weaknesses, and hiring recommendation."
        extra={
          <Button
            icon={<ReloadOutlined />}
            onClick={() => dispatch(reportsActions.fetchReportRequest(interviewId))}
          >
            Refresh
          </Button>
        }
      />

      <div className="grid gap-4 lg:grid-cols-[minmax(260px,320px)_1fr] lg:gap-6">
        <SectionCard title="Overall score" className="h-fit">
          <div className="flex flex-col items-center py-2">
            <Progress
              type="dashboard"
              percent={score}
              strokeColor={{ '0%': '#6366f1', '100%': '#a855f7' }}
              size={120}
            />
            <p className="mt-4 text-center text-2xl font-bold text-white">{score}/100</p>
          </div>
          <div className="mt-4 rounded-xl bg-white/[0.04] p-4">
            <p className="text-xs uppercase tracking-wider text-slate-500">Recommendation</p>
            <p className="mt-1 font-medium capitalize text-indigo-300">
              {current.recommendation}
            </p>
          </div>
        </SectionCard>

        <div className="space-y-4 lg:space-y-6">
          <SectionCard title="Summary">
            <Typography.Paragraph className="!mb-0 !text-slate-300 !leading-relaxed">
              {current.summary}
            </Typography.Paragraph>
          </SectionCard>

          <div className="grid gap-4 sm:grid-cols-2">
            <SectionCard title="Strengths">
              <Typography.Paragraph className="!mb-0 !text-sm !leading-relaxed !text-emerald-200/90 sm:!text-base">
                {current.strengths ?? '—'}
              </Typography.Paragraph>
            </SectionCard>
            <SectionCard title="Areas to improve">
              <Typography.Paragraph className="!mb-0 !text-sm !leading-relaxed !text-amber-200/90 sm:!text-base">
                {current.weaknesses ?? '—'}
              </Typography.Paragraph>
            </SectionCard>
          </div>
        </div>
      </div>
    </PageContainer>
  )
}
