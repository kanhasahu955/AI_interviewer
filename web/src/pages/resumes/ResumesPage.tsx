import { FileOutlined, InboxOutlined, EyeOutlined, AudioOutlined } from '@ant-design/icons'
import { Alert, App, Button, List, Upload, message } from 'antd'
import { useCallback, useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { useAppDispatch, useAppSelector } from '@/app/hooks'
import { EmptyState } from '@/components/common/EmptyState'
import { LoadingScreen } from '@/components/common/LoadingScreen'
import { PageContainer } from '@/components/common/PageContainer'
import { PageHeader } from '@/components/common/PageHeader'
import { SectionCard } from '@/components/common/SectionCard'
import { ResumeAnalyzerDrawer } from '@/components/resume/ResumeAnalyzerDrawer'
import { resumesActions } from '@/features/resumes/resumesSlice'
import { interviewsActions } from '@/features/interviews/interviewsSlice'
import { resumeService } from '@/services/ResumeService'
import { ApiError } from '@/core/errors/ApiError'
import {
  getResumeStatusBadgeClass,
  getResumeStatusLabel,
} from '@/utils/resumeStatus'
import type { ResumeAnalysisEvent, ResumePublic } from '@/types/api'

export function ResumesPage() {
  const dispatch = useAppDispatch()
  const navigate = useNavigate()
  const { notification } = App.useApp()
  const { items, uploading, loading, error } = useAppSelector((state) => state.resumes)
  const { actionLoading: startingInterview, createdInterviewId, error: interviewError } = useAppSelector(
    (state) => state.interviews,
  )
  const wasUploading = useRef(false)
  const pendingAutoAnalyze = useRef(false)
  const abortRef = useRef<AbortController | null>(null)
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [selectedResume, setSelectedResume] = useState<ResumePublic | null>(null)
  const [analyzing, setAnalyzing] = useState(false)
  const [analysisEvents, setAnalysisEvents] = useState<ResumeAnalysisEvent[]>([])
  const [analysisProgress, setAnalysisProgress] = useState(0)

  const runAnalysis = useCallback(async (resume: ResumePublic) => {
    abortRef.current?.abort()
    const controller = new AbortController()
    abortRef.current = controller

    setSelectedResume(resume)
    setDrawerOpen(true)
    setAnalyzing(true)
    setAnalysisEvents([])
    setAnalysisProgress(0)

    try {
      const result = await resumeService.analyzeStream(resume.id, {
        signal: controller.signal,
        onEvent: (event) => {
          setAnalysisEvents((prev) => [...prev, event])
          if (event.progress > 0) {
            setAnalysisProgress(event.progress)
          }
        },
      })
      setSelectedResume({ ...resume, parsed: result.parsed, ingested: result.ingested })
      dispatch(resumesActions.fetchResumesRequest())
      message.success(result.message)
    } catch (error) {
      if (error instanceof DOMException && error.name === 'AbortError') return
      message.error(
        error instanceof ApiError ? error.message : 'Analysis failed',
      )
    } finally {
      setAnalyzing(false)
      abortRef.current = null
    }
  }, [dispatch])

  const openAnalysis = useCallback(async (resume: ResumePublic) => {
    setSelectedResume(resume)
    setDrawerOpen(true)
    setAnalysisEvents([])

    if (resume.parsed?.analyzed_at || resume.parsed?.text_ready) {
      setAnalysisProgress(100)
      return
    }

    await runAnalysis(resume)
  }, [runAnalysis])

  useEffect(() => {
    dispatch(resumesActions.fetchResumesRequest())
  }, [dispatch])

  useEffect(() => {
    if (wasUploading.current && !uploading) {
      if (!error && pendingAutoAnalyze.current && items[0]) {
        pendingAutoAnalyze.current = false
        void runAnalysis(items[0])
      }
    }
    wasUploading.current = uploading
  }, [uploading, error, items, runAnalysis])

  useEffect(() => {
    return () => abortRef.current?.abort()
  }, [])

  useEffect(() => {
    if (interviewError) {
      notification.error({
        message: 'Could not start interview',
        description: interviewError,
        duration: 10,
        placement: 'top',
        style: { width: 480, maxWidth: '95vw' },
      })
    }
  }, [interviewError, notification])

  useEffect(() => {
    if (!createdInterviewId) return
    dispatch(interviewsActions.clearCreatedInterviewId())
    navigate(`/interviews/${createdInterviewId}/room`)
  }, [createdInterviewId, dispatch, navigate])

  const startAiInterview = (resumeId?: number) => {
    dispatch(
      interviewsActions.createSelfInterviewRequest(
        resumeId ? { resume_id: resumeId } : {},
      ),
    )
  }

  const handleCloseDrawer = () => {
    abortRef.current?.abort()
    setDrawerOpen(false)
    setAnalyzing(false)
  }

  return (
    <PageContainer>
      <PageHeader
        title="Resume analyzer"
        subtitle="Upload your resume and watch each analysis step live — like an AI agent trace."
      />

      {error ? <Alert type="error" message={error} showIcon className="mb-4" /> : null}
      {interviewError ? (
        <Alert
          type="error"
          showIcon
          className="mb-4"
          message="Interview could not start"
          description={interviewError}
        />
      ) : null}

      <SectionCard title="Upload resume" className="mb-6">
        <Upload.Dragger
          multiple={false}
          showUploadList={false}
          disabled={uploading || analyzing}
          beforeUpload={(file) => {
            pendingAutoAnalyze.current = true
            dispatch(resumesActions.uploadResumeRequest(file))
            return false
          }}
        >
          <p className="ant-upload-drag-icon !text-indigo-400">
            <InboxOutlined className="!text-4xl" />
          </p>
          <p className="ant-upload-text !text-white">
            {uploading
              ? 'Uploading file…'
              : analyzing
                ? 'Analysis in progress…'
                : 'Click or drag a resume here'}
          </p>
          <p className="ant-upload-hint !text-slate-500">
            PDF or DOCX · Live step-by-step analysis stream
          </p>
        </Upload.Dragger>
      </SectionCard>

      {items.length > 0 ? (
        <SectionCard title="Ready for your AI interview?" className="mb-6">
          <p className="mb-4 text-sm text-slate-400">
            Start a live voice interview — the AI reads your resume, asks questions via
            LiveKit + Whisper, and saves every Q&amp;A to your profile.
          </p>
          <Button
            type="primary"
            size="large"
            icon={<AudioOutlined />}
            loading={startingInterview}
            onClick={() => startAiInterview(items[0]?.id)}
          >
            Start AI voice interview
          </Button>
        </SectionCard>
      ) : null}

      {loading && items.length === 0 ? (
        <LoadingScreen />
      ) : items.length === 0 ? (
        <EmptyState description="Upload a resume to get started" />
      ) : (
        <SectionCard title={`Your resumes (${items.length})`}>
          <List
            dataSource={items}
            renderItem={(resume: ResumePublic) => (
              <List.Item className="!border-white/[0.04] !px-0">
                <div className="flex w-full flex-col gap-3 rounded-xl bg-white/[0.03] p-4 sm:flex-row sm:items-center">
                  <div className="flex min-w-0 flex-1 items-start gap-4">
                    <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-indigo-500/15 text-indigo-300">
                      <FileOutlined />
                    </div>
                    <div className="min-w-0">
                      <p className="truncate font-medium text-white">{resume.file_name}</p>
                      <p className="mt-1 text-sm text-slate-400">ID {resume.id}</p>
                    </div>
                  </div>
                  <div className="flex flex-wrap items-center gap-2">
                    <span
                      className={`rounded-full px-2.5 py-1 text-xs ${getResumeStatusBadgeClass(resume)}`}
                    >
                      {getResumeStatusLabel(resume)}
                    </span>
                    <Button
                      icon={<EyeOutlined />}
                      loading={analyzing && selectedResume?.id === resume.id}
                      onClick={() =>
                        resume.parsed?.analyzed_at || resume.parsed?.text_ready
                          ? openAnalysis(resume)
                          : runAnalysis(resume)
                      }
                    >
                      {resume.parsed?.analyzed_at ? 'View analysis' : 'Analyze'}
                    </Button>
                    <Button
                      icon={<AudioOutlined />}
                      loading={startingInterview}
                      onClick={() => startAiInterview(resume.id)}
                    >
                      Interview
                    </Button>
                  </div>
                </div>
              </List.Item>
            )}
          />
        </SectionCard>
      )}

      <ResumeAnalyzerDrawer
        resume={selectedResume}
        open={drawerOpen}
        analyzing={analyzing}
        events={analysisEvents}
        progress={analysisProgress}
        onClose={handleCloseDrawer}
        onReanalyze={
          selectedResume ? () => void runAnalysis(selectedResume) : undefined
        }
        onStartInterview={
          selectedResume
            ? () => startAiInterview(selectedResume.id)
            : undefined
        }
        startingInterview={startingInterview}
      />
    </PageContainer>
  )
}
