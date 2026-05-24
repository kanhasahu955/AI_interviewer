import { AudioOutlined } from '@ant-design/icons'
import { Button, Drawer, Tag, Typography } from 'antd'

import { ResumeAnalysisTimeline } from '@/components/resume/ResumeAnalysisTimeline'
import type { ResumeAnalysisEvent, ResumePublic } from '@/types/api'

interface ResumeAnalyzerDrawerProps {
  resume: ResumePublic | null
  open: boolean
  analyzing?: boolean
  events: ResumeAnalysisEvent[]
  progress: number
  onClose: () => void
  onReanalyze?: () => void
  onStartInterview?: () => void
  startingInterview?: boolean
}

export function ResumeAnalyzerDrawer({
  resume,
  open,
  analyzing,
  events,
  progress,
  onClose,
  onReanalyze,
  onStartInterview,
  startingInterview,
}: ResumeAnalyzerDrawerProps) {
  const parsed = resume?.parsed ?? {}
  const skills = (parsed.skills_detected as string[]) ?? []
  const sections = (parsed.sections_found as string[]) ?? []
  const preview = String(parsed.preview ?? '')
  const showTimeline = analyzing || events.length > 0
  const showResults = resume && !analyzing

  return (
    <Drawer
      title={resume ? `Resume analysis · ${resume.file_name}` : 'Resume analysis'}
      open={open}
      onClose={onClose}
      width={Math.min(720, window.innerWidth - 24)}
      extra={
        <div className="flex gap-2">
          {resume && onStartInterview ? (
            <Button
              type="primary"
              size="small"
              icon={<AudioOutlined />}
              loading={startingInterview}
              onClick={onStartInterview}
            >
              Start AI interview
            </Button>
          ) : null}
          {resume && onReanalyze ? (
            <Button size="small" loading={analyzing} onClick={onReanalyze}>
              Re-run analysis
            </Button>
          ) : null}
        </div>
      }
    >
      {showTimeline ? (
        <div className="mb-6">
          <ResumeAnalysisTimeline
            events={events}
            active={Boolean(analyzing)}
            progress={progress}
          />
        </div>
      ) : null}

      {showResults ? (
        <div className="space-y-6">
          <div className="flex flex-wrap gap-2">
            <Tag color={parsed.text_ready ? 'green' : 'orange'}>
              {parsed.text_ready ? 'Text extracted' : 'No text extracted'}
            </Tag>
            <Tag color={resume.ingested ? 'purple' : 'blue'}>
              {resume.ingested ? 'Indexed for AI interviews' : 'Ready for scheduling'}
            </Tag>
          </div>

          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
            {(
              [
                ['Words', parsed.word_count],
                ['Characters', parsed.char_count],
                ['Skills found', skills.length],
              ] as Array<[string, string | number | undefined]>
            ).map(([label, value]) => (
              <div key={String(label)} className="rounded-xl bg-white/5 p-3">
                <p className="text-xs text-slate-500">{label}</p>
                <p className="text-lg font-semibold text-white">{String(value ?? '—')}</p>
              </div>
            ))}
          </div>

          {sections.length > 0 ? (
            <div>
              <Typography.Title level={5} className="!text-white">
                Sections detected
              </Typography.Title>
              <div className="flex flex-wrap gap-2">
                {sections.map((s) => (
                  <Tag key={s}>{s}</Tag>
                ))}
              </div>
            </div>
          ) : null}

          {skills.length > 0 ? (
            <div>
              <Typography.Title level={5} className="!text-white">
                Skills detected
              </Typography.Title>
              <div className="flex flex-wrap gap-2">
                {skills.map((skill) => (
                  <Tag key={skill} color="processing">
                    {skill}
                  </Tag>
                ))}
              </div>
            </div>
          ) : null}

          {preview ? (
            <div>
              <Typography.Title level={5} className="!text-white">
                Text preview
              </Typography.Title>
              <pre className="max-h-[360px] overflow-auto rounded-xl bg-black/30 p-4 text-xs leading-relaxed text-slate-300 whitespace-pre-wrap">
                {preview}
              </pre>
            </div>
          ) : (
            <Typography.Paragraph className="!text-slate-400">
              No preview available. Try re-uploading as PDF or DOCX.
            </Typography.Paragraph>
          )}
        </div>
      ) : analyzing ? null : (
        <Typography.Paragraph className="!text-slate-400">
          Run analysis to see extracted skills and preview text.
        </Typography.Paragraph>
      )}
    </Drawer>
  )
}
