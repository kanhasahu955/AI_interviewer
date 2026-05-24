import { PlusOutlined } from '@ant-design/icons'
import { Alert, Button, Col, Input, Row, Segmented } from 'antd'
import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'

import { useAppDispatch, useAppSelector } from '@/app/hooks'
import { EmptyState } from '@/components/common/EmptyState'
import { LoadingScreen } from '@/components/common/LoadingScreen'
import { PageContainer } from '@/components/common/PageContainer'
import { PageHeader } from '@/components/common/PageHeader'
import { InterviewCard } from '@/components/interview/InterviewCard'
import { interviewsActions } from '@/features/interviews/interviewsSlice'
import type { InterviewStatus } from '@/types/api'

type FilterKey = 'all' | InterviewStatus

const FILTER_OPTIONS: { label: string; value: FilterKey }[] = [
  { label: 'All', value: 'all' },
  { label: 'Scheduled', value: 'scheduled' },
  { label: 'Live', value: 'live' },
  { label: 'Completed', value: 'completed' },
  { label: 'Flagged', value: 'flagged' },
]

export function InterviewListPage() {
  const dispatch = useAppDispatch()
  const { items, loading, error } = useAppSelector((state) => state.interviews)
  const role = useAppSelector((state) => state.auth.user?.role)
  const [filter, setFilter] = useState<FilterKey>('all')
  const [search, setSearch] = useState('')

  useEffect(() => {
    dispatch(interviewsActions.fetchInterviewsRequest())
  }, [dispatch])

  const filtered = useMemo(() => {
    return items.filter((item) => {
      const matchesFilter = filter === 'all' || item.status === filter
      const query = search.trim().toLowerCase()
      const matchesSearch =
        !query ||
        String(item.id).includes(query) ||
        String(item.jd_id).includes(query) ||
        item.status.includes(query)
      return matchesFilter && matchesSearch
    })
  }, [items, filter, search])

  return (
    <PageContainer>
      <PageHeader
        title="Interviews"
        subtitle="Browse, filter, and manage all your interview sessions."
        extra={
          role === 'recruiter' || role === 'admin' ? (
            <Link to="/interviews/new">
              <Button type="primary" icon={<PlusOutlined />} size="large">
                Schedule
              </Button>
            </Link>
          ) : null
        }
      />

      {error ? <Alert type="error" message={error} showIcon className="mb-4" /> : null}

      <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <Segmented
          options={FILTER_OPTIONS}
          value={filter}
          onChange={(value) => setFilter(value as FilterKey)}
          className="!overflow-x-auto"
        />
        <Input.Search
          placeholder="Search by ID, JD, status…"
          allowClear
          onChange={(e) => setSearch(e.target.value)}
          className="w-full sm:max-w-xs"
        />
      </div>

      {loading ? (
        <LoadingScreen />
      ) : filtered.length === 0 ? (
        <EmptyState
          description={items.length ? 'No interviews match your filters' : 'No interviews yet'}
          action={
            (role === 'recruiter' || role === 'admin') && !items.length ? (
              <Link to="/interviews/new">
                <Button type="primary" icon={<PlusOutlined />}>
                  Schedule interview
                </Button>
              </Link>
            ) : undefined
          }
        />
      ) : (
        <Row gutter={[12, 12]}>
          {filtered.map((interview) => (
            <Col xs={24} sm={12} xl={8} key={interview.id}>
              <InterviewCard interview={interview} />
            </Col>
          ))}
        </Row>
      )}
    </PageContainer>
  )
}
