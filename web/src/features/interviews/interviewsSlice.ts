import { createSlice, type PayloadAction } from '@reduxjs/toolkit'

import type {
  InterviewCreate,
  InterviewPublic,
  InterviewSelfCreate,
  LiveKitTokenResponse,
  ProctorEventPublic,
  TurnPublic,
  WsEnvelope,
} from '@/types/api'
import type { WebSocketStatus } from '@/core/websocket/WebSocketClient'

export interface TranscriptEntry {
  id: string
  role: string
  content: string
  channel?: string
  ts: number
  portraitUrl?: string | null
  emotion?: string | null
}

export interface ProctorEntry {
  id: string
  kind: string
  severity: string
  ts: number
  payload?: Record<string, unknown> | null
}

export interface InterviewsState {
  items: InterviewPublic[]
  selected: InterviewPublic | null
  turns: TurnPublic[]
  liveKit: LiveKitTokenResponse | null
  transcript: TranscriptEntry[]
  proctorEvents: ProctorEntry[]
  wsStatus: WebSocketStatus
  loading: boolean
  detailLoading: boolean
  actionLoading: boolean
  tokenLoading: boolean
  error: string | null
  createdInterviewId: number | null
}

const initialState: InterviewsState = {
  items: [],
  selected: null,
  turns: [],
  liveKit: null,
  transcript: [],
  proctorEvents: [],
  wsStatus: 'idle',
  loading: false,
  detailLoading: false,
  actionLoading: false,
  tokenLoading: false,
  error: null,
  createdInterviewId: null,
}

const interviewsSlice = createSlice({
  name: 'interviews',
  initialState,
  reducers: {
    fetchInterviewsRequest(state) {
      state.loading = true
      state.error = null
    },
    fetchInterviewsSuccess(state, action: PayloadAction<InterviewPublic[]>) {
      state.loading = false
      state.items = action.payload
    },
    fetchInterviewsFailure(state, action: PayloadAction<string>) {
      state.loading = false
      state.error = action.payload
    },
    fetchInterviewRequest(state, _action: PayloadAction<number>) {
      state.detailLoading = true
      state.error = null
    },
    fetchInterviewSuccess(
      state,
      action: PayloadAction<{ interview: InterviewPublic; turns: TurnPublic[] }>,
    ) {
      state.detailLoading = false
      state.selected = action.payload.interview
      state.turns = action.payload.turns
    },
    fetchInterviewFailure(state, action: PayloadAction<string>) {
      state.detailLoading = false
      state.error = action.payload
    },
    createInterviewRequest(state, _action: PayloadAction<InterviewCreate>) {
      state.actionLoading = true
      state.error = null
    },
    createInterviewSuccess(state, action: PayloadAction<InterviewPublic>) {
      state.actionLoading = false
      state.items = [action.payload, ...state.items]
      state.createdInterviewId = action.payload.id
    },
    createInterviewFailure(state, action: PayloadAction<string>) {
      state.actionLoading = false
      state.error = action.payload
    },
    createSelfInterviewRequest(state, _action: PayloadAction<InterviewSelfCreate>) {
      state.actionLoading = true
      state.error = null
    },
    createSelfInterviewSuccess(state, action: PayloadAction<InterviewPublic>) {
      state.actionLoading = false
      state.items = [action.payload, ...state.items]
      state.createdInterviewId = action.payload.id
    },
    createSelfInterviewFailure(state, action: PayloadAction<string>) {
      state.actionLoading = false
      state.error = action.payload
    },
    fetchTurnsSuccess(state, action: PayloadAction<TurnPublic[]>) {
      state.turns = action.payload
    },
    endInterviewRequest(state, _action: PayloadAction<number>) {
      state.actionLoading = true
    },
    endInterviewSuccess(state, action: PayloadAction<InterviewPublic>) {
      state.actionLoading = false
      state.selected = action.payload
      state.items = state.items.map((item) =>
        item.id === action.payload.id ? action.payload : item,
      )
    },
    endInterviewFailure(state, action: PayloadAction<string>) {
      state.actionLoading = false
      state.error = action.payload
    },
    fetchLiveKitTokenRequest(state, _action: PayloadAction<number>) {
      state.tokenLoading = true
      state.error = null
    },
    fetchLiveKitTokenSuccess(state, action: PayloadAction<LiveKitTokenResponse>) {
      state.tokenLoading = false
      state.liveKit = action.payload
    },
    fetchLiveKitTokenFailure(state, action: PayloadAction<string>) {
      state.tokenLoading = false
      state.error = action.payload
    },
    clearLiveKit(state) {
      state.liveKit = null
    },
    setWsStatus(state, action: PayloadAction<WebSocketStatus>) {
      state.wsStatus = action.payload
    },
    appendTranscript(state, action: PayloadAction<WsEnvelope>) {
      const data = action.payload.data
      if (!data?.content) return
      state.transcript.push({
        id: `${Date.now()}-${state.transcript.length}`,
        role: data.role ?? 'system',
        content: data.content,
        channel: action.payload.channel,
        ts: Date.now(),
      })
    },
    processWsEnvelope(state, action: PayloadAction<WsEnvelope>) {
      const channel = String(action.payload.channel ?? '')
      const data = action.payload.data ?? {}

      if (channel.includes('proctor') || data.kind) {
        state.proctorEvents.push({
          id: `${Date.now()}-p-${state.proctorEvents.length}`,
          kind: String(data.kind ?? 'custom'),
          severity: String(data.severity ?? 'info'),
          ts: Date.now(),
          payload: (data.payload as Record<string, unknown>) ?? data,
        })
        return
      }

      if (channel.includes('portrait') || data.url) {
        const content = data.content ? String(data.content) : undefined
        const matchIdx = content
          ? state.transcript.findLastIndex(
              (e) => e.role === 'assistant' && e.content === content,
            )
          : -1
        const idx =
          matchIdx >= 0 ? matchIdx : state.transcript.findLastIndex((e) => e.role === 'assistant')
        if (idx >= 0) {
          state.transcript[idx] = {
            ...state.transcript[idx],
            portraitUrl: String(data.url),
            emotion: data.emotion ? String(data.emotion) : state.transcript[idx].emotion,
          }
        }
        return
      }

      if (data.content) {
        state.transcript.push({
          id: `${Date.now()}-t-${state.transcript.length}`,
          role: String(data.role ?? 'system'),
          content: String(data.content),
          channel: action.payload.channel,
          ts: Date.now(),
          portraitUrl: data.portrait_url ? String(data.portrait_url) : undefined,
          emotion: data.emotion ? String(data.emotion) : undefined,
        })
      }
    },
    setProctorEvents(state, action: PayloadAction<ProctorEventPublic[]>) {
      state.proctorEvents = action.payload.map((evt, idx) => ({
        id: String(evt.id ?? idx),
        kind: evt.kind,
        severity: evt.severity,
        ts: new Date(evt.ts).getTime(),
        payload: evt.payload,
      }))
    },
    clearLiveSession(state) {
      state.transcript = []
      state.proctorEvents = []
      state.wsStatus = 'idle'
    },
    clearCreatedInterviewId(state) {
      state.createdInterviewId = null
    },
    resetSession(state) {
      state.selected = null
      state.turns = []
      state.liveKit = null
      state.transcript = []
      state.proctorEvents = []
      state.wsStatus = 'idle'
      state.createdInterviewId = null
      state.tokenLoading = false
      state.actionLoading = false
    },
  },
})

export const interviewsActions = interviewsSlice.actions
export const interviewsReducer = interviewsSlice.reducer
