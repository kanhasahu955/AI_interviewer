import { Alert, Button, Form, Input } from 'antd'
import { useEffect } from 'react'

import { useAppDispatch, useAppSelector } from '@/app/hooks'
import { EmptyState } from '@/components/common/EmptyState'
import { LoadingScreen } from '@/components/common/LoadingScreen'
import { PageContainer } from '@/components/common/PageContainer'
import { PageHeader } from '@/components/common/PageHeader'
import { SectionCard } from '@/components/common/SectionCard'
import { jdsActions } from '@/features/jds/jdsSlice'
import type { JDPublic } from '@/types/api'

export function JdsPage() {
  const dispatch = useAppDispatch()
  const { items, loading, creating, error } = useAppSelector((state) => state.jds)

  useEffect(() => {
    dispatch(jdsActions.fetchJdsRequest())
  }, [dispatch])

  return (
    <PageContainer>
      <PageHeader
        title="Job descriptions"
        subtitle="Create and manage JDs that drive AI interview questioning."
      />

      {error ? <Alert type="error" message={error} showIcon className="mb-4" /> : null}

      <div className="grid gap-6 lg:grid-cols-[minmax(280px,360px)_1fr]">
        <SectionCard title="New JD" className="h-fit lg:sticky lg:top-20">
          <Form
            layout="vertical"
            onFinish={(values) => dispatch(jdsActions.createJdRequest(values))}
          >
            <Form.Item label="Title" name="title" rules={[{ required: true }]}>
              <Input size="large" placeholder="Senior Backend Engineer" />
            </Form.Item>
            <Form.Item label="Company" name="company">
              <Input size="large" placeholder="Acme Corp" />
            </Form.Item>
            <Form.Item label="Seniority" name="seniority">
              <Input size="large" placeholder="Senior" />
            </Form.Item>
            <Form.Item label="Description" name="raw_text" rules={[{ required: true }]}>
              <Input.TextArea rows={6} placeholder="Paste the full job description…" />
            </Form.Item>
            <Button type="primary" htmlType="submit" loading={creating} block size="large">
              Save JD
            </Button>
          </Form>
        </SectionCard>

        <div>
          {loading ? (
            <LoadingScreen />
          ) : items.length === 0 ? (
            <EmptyState description="No job descriptions yet" />
          ) : (
            <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-1">
              {items.map((jd: JDPublic) => (
                <SectionCard key={jd.id}>
                  <h3 className="text-lg font-semibold text-white">{jd.title}</h3>
                  <p className="mt-1 text-sm text-slate-400">
                    {[jd.company, jd.seniority].filter(Boolean).join(' · ') || '—'}
                  </p>
                  <p className="mt-3 line-clamp-4 text-sm leading-relaxed text-slate-300">
                    {jd.raw_text}
                  </p>
                  <div className="mt-4 flex flex-wrap gap-2">
                    <span className="rounded-full bg-white/5 px-2.5 py-1 text-xs text-slate-400">
                      ID {jd.id}
                    </span>
                    <span
                      className={`rounded-full px-2.5 py-1 text-xs ${
                        jd.ingested
                          ? 'bg-emerald-500/15 text-emerald-300'
                          : 'bg-amber-500/15 text-amber-300'
                      }`}
                    >
                      {jd.ingested ? 'Ingested' : 'Processing'}
                    </span>
                  </div>
                </SectionCard>
              ))}
            </div>
          )}
        </div>
      </div>
    </PageContainer>
  )
}
