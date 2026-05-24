import { Alert, Button, Form, Select } from 'antd'
import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { useAppDispatch, useAppSelector } from '@/app/hooks'
import { CandidateSelect } from '@/components/interview/CandidateSelect'
import { PageContainer } from '@/components/common/PageContainer'
import { PageHeader } from '@/components/common/PageHeader'
import { SectionCard } from '@/components/common/SectionCard'
import { interviewsActions } from '@/features/interviews/interviewsSlice'
import { jdsActions } from '@/features/jds/jdsSlice'
import { resumeService } from '@/services/ResumeService'
import { getResumeStatusLabel } from '@/utils/resumeStatus'
import type { ResumePublic } from '@/types/api'

export function InterviewCreatePage() {
  const dispatch = useAppDispatch()
  const navigate = useNavigate()
  const [form] = Form.useForm()
  const candidateId = Form.useWatch('candidate_id', form)
  const [candidateResumes, setCandidateResumes] = useState<ResumePublic[]>([])
  const [resumesLoading, setResumesLoading] = useState(false)
  const { actionLoading, error, createdInterviewId } = useAppSelector(
    (state) => state.interviews,
  )
  const jds = useAppSelector((state) => state.jds.items)

  useEffect(() => {
    dispatch(interviewsActions.clearCreatedInterviewId())
    dispatch(jdsActions.fetchJdsRequest())
  }, [dispatch])

  useEffect(() => {
    if (!createdInterviewId) return
    navigate(`/interviews/${createdInterviewId}`, { replace: true })
    dispatch(interviewsActions.clearCreatedInterviewId())
  }, [createdInterviewId, navigate, dispatch])

  useEffect(() => {
    form.setFieldValue('resume_id', undefined)

    if (!candidateId) {
      setCandidateResumes([])
      return
    }

    let cancelled = false
    setResumesLoading(true)
    resumeService
      .list(candidateId)
      .then((resumes) => {
        if (!cancelled) setCandidateResumes(resumes)
      })
      .catch(() => {
        if (!cancelled) setCandidateResumes([])
      })
      .finally(() => {
        if (!cancelled) setResumesLoading(false)
      })

    return () => {
      cancelled = true
    }
  }, [candidateId, form])

  return (
    <PageContainer>
      <PageHeader
        title="Schedule interview"
        subtitle="Search for a candidate, pick a JD, and optionally attach their resume."
      />

      {error ? <Alert type="error" message={error} showIcon className="mb-4" /> : null}

      <SectionCard title="Interview details" className="max-w-2xl">
        <Form
          form={form}
          layout="vertical"
          requiredMark={false}
          onFinish={(values) =>
            dispatch(interviewsActions.createInterviewRequest(values))
          }
          initialValues={{ duration_minutes: 30 }}
          className="!mt-1"
        >
          <Form.Item
            label="Candidate"
            name="candidate_id"
            rules={[{ required: true, message: 'Select a candidate' }]}
          >
            <CandidateSelect />
          </Form.Item>

          <Form.Item label="Job description" name="jd_id" rules={[{ required: true }]}>
            <Select
              size="large"
              options={jds.map((jd) => ({
                value: jd.id,
                label: `${jd.title}${jd.company ? ` · ${jd.company}` : ''}`,
              }))}
              placeholder="Select a JD"
            />
          </Form.Item>

          <Form.Item label="Resume (optional)" name="resume_id">
            <Select
              size="large"
              allowClear
              loading={resumesLoading}
              disabled={!candidateId || candidateResumes.length === 0}
              placeholder={
                !candidateId
                  ? 'Choose a candidate first'
                  : candidateResumes.length
                    ? 'Select a resume'
                    : 'No resumes for this candidate'
              }
              options={candidateResumes.map((resume) => ({
                value: resume.id,
                label: `${resume.file_name} · ${getResumeStatusLabel(resume)}`,
              }))}
            />
          </Form.Item>

          <Form.Item label="Duration" name="duration_minutes">
            <Select
              size="large"
              options={[15, 30, 45, 60, 90].map((minutes) => ({
                value: minutes,
                label: `${minutes} minutes`,
              }))}
            />
          </Form.Item>

          <Button type="primary" htmlType="submit" loading={actionLoading} size="large" block className="sm:!w-auto">
            Create interview
          </Button>
        </Form>
      </SectionCard>
    </PageContainer>
  )
}
