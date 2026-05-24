import {
  CalendarOutlined,
  CheckCircleOutlined,
  FileTextOutlined,
  PlayCircleOutlined,
  PlusOutlined,
  ReadOutlined,
  ScheduleOutlined,
  UploadOutlined,
} from '@ant-design/icons'
import { Button, Col, Row } from 'antd'
import type { ReactNode } from 'react'
import { useEffect } from 'react'
import { Link } from 'react-router-dom'

import { useAppDispatch, useAppSelector } from '@/app/hooks'
import { LoadingScreen } from '@/components/common/LoadingScreen'
import { PageContainer } from '@/components/common/PageContainer'
import { PageHeader } from '@/components/common/PageHeader'
import { QuickAction } from '@/components/common/QuickAction'
import { SectionCard } from '@/components/common/SectionCard'
import { StatCard } from '@/components/common/StatCard'
import { InterviewCard } from '@/components/interview/InterviewCard'
import { interviewsActions } from '@/features/interviews/interviewsSlice'
import type { UserRole } from '@/types/api'

const QUICK_ACTIONS: Record<
  UserRole,
  Array<{ to: string; title: string; description: string; icon: ReactNode }>
> = {
  candidate: [
    {
      to: '/interviews',
      title: 'My interviews',
      description: 'View scheduled and completed sessions',
      icon: <ScheduleOutlined />,
    },
    {
      to: '/resumes',
      title: 'Upload resume',
      description: 'Add your resume for AI-powered questions',
      icon: <UploadOutlined />,
    },
  ],
  recruiter: [
    {
      to: '/interviews/new',
      title: 'Schedule interview',
      description: 'Pair a candidate with a job description',
      icon: <PlusOutlined />,
    },
    {
      to: '/jds',
      title: 'Manage JDs',
      description: 'Create and edit job descriptions',
      icon: <ReadOutlined />,
    },
  ],
  admin: [
    {
      to: '/interviews/new',
      title: 'Schedule interview',
      description: 'Create a new interview session',
      icon: <PlusOutlined />,
    },
    {
      to: '/jds',
      title: 'Job descriptions',
      description: 'Manage hiring requirements',
      icon: <ReadOutlined />,
    },
    {
      to: '/resumes',
      title: 'All resumes',
      description: 'Browse candidate uploads',
      icon: <FileTextOutlined />,
    },
  ],
}

export function DashboardPage() {
  const dispatch = useAppDispatch()
  const user = useAppSelector((state) => state.auth.user)
  const { items, loading } = useAppSelector((state) => state.interviews)
  const role = user?.role ?? 'candidate'

  useEffect(() => {
    dispatch(interviewsActions.fetchInterviewsRequest())
  }, [dispatch])

  const upcoming = items.filter((i) => i.status === 'scheduled' || i.status === 'live')
  const completed = items.filter((i) => i.status === 'completed')
  const live = items.filter((i) => i.status === 'live')
  const nextInterview = upcoming[0]

  return (
    <PageContainer>
      {(role === 'candidate' || role === 'admin') && nextInterview ? (
        <div className="mb-6 overflow-hidden rounded-2xl border border-emerald-500/30 bg-gradient-to-br from-emerald-600/20 via-indigo-600/10 to-transparent p-5 sm:mb-8 sm:p-8">
          <p className="text-sm font-medium text-emerald-300">Ready to interview</p>
          <h2 className="mt-1 text-xl font-bold text-white sm:text-2xl">
            {nextInterview.status === 'live' ? 'Your session is live' : 'You have an upcoming interview'}
          </h2>
          <p className="mt-2 max-w-xl text-sm text-slate-400">
            Session #{nextInterview.id} · {nextInterview.duration_minutes} minutes · JD #
            {nextInterview.jd_id}
          </p>
          <Link to={`/interviews/${nextInterview.id}/room`} className="mt-5 inline-block">
            <Button type="primary" size="large" icon={<PlayCircleOutlined />}>
              {nextInterview.status === 'live' ? 'Rejoin interview room' : 'Start interview'}
            </Button>
          </Link>
        </div>
      ) : null}

      <div className="mb-6 overflow-hidden rounded-2xl border border-white/[0.08] bg-gradient-to-br from-indigo-600/20 via-violet-600/10 to-transparent p-5 sm:mb-8 sm:p-8">
        <p className="text-sm font-medium text-indigo-300">Your workspace</p>
        <h1 className="mt-1 text-balance text-2xl font-bold text-white sm:text-3xl lg:text-4xl">
          Hello, {user?.full_name?.split(' ')[0] ?? 'there'}
        </h1>
        <p className="mt-2 max-w-2xl text-sm text-slate-400 sm:text-base">
          {role.charAt(0).toUpperCase() + role.slice(1)} dashboard — track interviews,
          manage assets, and jump back in.
        </p>
        {(role === 'recruiter' || role === 'admin') && (
          <Link to="/interviews/new" className="mt-5 inline-block">
            <Button type="primary" size="large" icon={<PlusOutlined />}>
              Schedule interview
            </Button>
          </Link>
        )}
      </div>

      <Row gutter={[12, 12]} className="mb-6 sm:mb-8">
        <Col xs={12} sm={12} lg={6}>
          <StatCard
            label="Total"
            value={items.length}
            icon={<ScheduleOutlined />}
            accent="indigo"
          />
        </Col>
        <Col xs={12} sm={12} lg={6}>
          <StatCard
            label="Upcoming"
            value={upcoming.length}
            icon={<CalendarOutlined />}
            accent="violet"
            trend={live.length ? `${live.length} live now` : undefined}
          />
        </Col>
        <Col xs={12} sm={12} lg={6}>
          <StatCard
            label="Completed"
            value={completed.length}
            icon={<CheckCircleOutlined />}
            accent="emerald"
          />
        </Col>
        <Col xs={12} sm={12} lg={6}>
          <StatCard
            label="Completion rate"
            value={items.length ? `${Math.round((completed.length / items.length) * 100)}%` : '—'}
            icon={<CheckCircleOutlined />}
            accent="amber"
          />
        </Col>
      </Row>

      <SectionCard title="Quick actions" className="mb-6 sm:mb-8">
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {(QUICK_ACTIONS[role] ?? QUICK_ACTIONS.candidate).map((action) => (
            <QuickAction key={action.to} {...action} />
          ))}
        </div>
      </SectionCard>

      <PageHeader
        title="Recent interviews"
        subtitle="Your latest sessions at a glance."
        extra={
          <Link to="/interviews">
            <Button type="link">View all</Button>
          </Link>
        }
      />

      {loading ? (
        <LoadingScreen />
      ) : items.length === 0 ? (
        <SectionCard>
          <div className="py-8 text-center text-slate-400">
            <p>No interviews yet.</p>
            {(role === 'recruiter' || role === 'admin') && (
              <Link to="/interviews/new" className="mt-3 inline-block">
                <Button type="primary" icon={<PlusOutlined />}>
                  Schedule your first interview
                </Button>
              </Link>
            )}
          </div>
        </SectionCard>
      ) : (
        <Row gutter={[12, 12]}>
          {items.slice(0, 6).map((interview) => (
            <Col xs={24} sm={12} xl={8} key={interview.id}>
              <InterviewCard interview={interview} />
            </Col>
          ))}
        </Row>
      )}
    </PageContainer>
  )
}
