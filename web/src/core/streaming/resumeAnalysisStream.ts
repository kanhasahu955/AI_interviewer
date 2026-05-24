import { API_PREFIX, env } from '@/core/config/env'
import { ApiError } from '@/core/errors/ApiError'
import { TokenStorage } from '@/core/http/TokenStorage'
import type { ResumeAnalysisEvent, ResumeAnalyzeResponse } from '@/types/api'

export interface ResumeAnalysisStreamHandlers {
  onEvent: (event: ResumeAnalysisEvent) => void
  signal?: AbortSignal
}

function parseSseChunk(
  buffer: string,
  onEvent: (event: ResumeAnalysisEvent) => void,
): string {
  const frames = buffer.split('\n\n')
  const remainder = frames.pop() ?? ''

  for (const frame of frames) {
    if (!frame.trim()) continue

    let eventType = 'message'
    let dataLine = ''

    for (const line of frame.split('\n')) {
      if (line.startsWith('event:')) {
        eventType = line.slice(6).trim()
      } else if (line.startsWith('data:')) {
        dataLine += line.slice(5).trim()
      }
    }

    if (!dataLine) continue

    try {
      const payload = JSON.parse(dataLine) as ResumeAnalysisEvent
      onEvent({ ...payload, type: payload.type || eventType })
    } catch {
      onEvent({
        type: eventType,
        step: 'parse',
        message: dataLine,
        progress: 0,
        status: 'error',
      })
    }
  }

  return remainder
}

export async function streamResumeAnalysis(
  resumeId: number,
  handlers: ResumeAnalysisStreamHandlers,
): Promise<ResumeAnalyzeResponse> {
  const token = TokenStorage.getInstance().get()
  const response = await fetch(
    `${env.apiBaseUrl}${API_PREFIX}/resumes/${resumeId}/analyze/stream`,
    {
      method: 'POST',
      headers: {
        Accept: 'text/event-stream',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      signal: handlers.signal,
    },
  )

  if (!response.ok) {
    let message = `Analysis stream failed (${response.status})`
    try {
      const body = (await response.json()) as { error?: { message?: string } }
      message = body.error?.message ?? message
    } catch {
      /* ignore */
    }
    throw new ApiError(message, { status: response.status })
  }

  if (!response.body) {
    throw new ApiError('No stream body received', { status: 500 })
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  let result: ResumeAnalyzeResponse | null = null
  let streamError: ApiError | null = null

  const handleEvent = (event: ResumeAnalysisEvent) => {
    handlers.onEvent(event)
    if (event.type === 'error') {
      streamError = new ApiError(event.message || 'Analysis failed', { status: 500 })
    }
    if (event.type === 'result' && event.detail) {
      const detail = event.detail
      result = {
        id: Number(detail.id),
        file_name: String(detail.file_name ?? ''),
        ingested: Boolean(detail.ingested),
        parsed: (detail.parsed as Record<string, unknown>) ?? {},
        message: String(detail.message ?? event.message),
      }
    }
  }

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })
    buffer = parseSseChunk(buffer, handleEvent)
  }

  if (buffer.trim()) {
    parseSseChunk(`${buffer}\n\n`, handleEvent)
  }

  if (streamError) throw streamError

  if (!result) {
    throw new ApiError('Analysis finished without a result', { status: 500 })
  }

  return result
}
