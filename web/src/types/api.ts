export type UserRole = 'candidate' | 'recruiter' | 'admin'

export type InterviewStatus =
  | 'scheduled'
  | 'live'
  | 'completed'
  | 'cancelled'
  | 'flagged'

export interface SignupRequest {
  email: string
  password: string
  full_name?: string | null
  role?: UserRole
}

export interface LoginRequest {
  email: string
  password: string
  otp_code?: string | null
}

export interface OtpRequestPayload {
  email: string
}

export interface OtpVerifyRequest {
  code: string
  email?: string | null
}

export interface ApiErrorPayload {
  error: {
    code: string
    message: string
    request_id?: string
    details?: unknown
  }
}

export interface TokenResponse {
  access_token: string
  token_type: string
  user_id: number
  role: UserRole
}

export interface OtpChallengeResponse {
  otp_required: boolean
  delivery: 'email' | 'totp'
  sent_to: string | null
  expires_in_seconds: number
  message: string
}

export interface OtpEnrolResponse {
  mode: string
  expires_in_seconds: number
  sent_to?: string | null
  secret?: string | null
  otpauth_uri?: string | null
  message: string
}

export interface UserPublic {
  id: number
  email: string
  full_name: string | null
  role: UserRole
  is_active: boolean
  otp_enabled: boolean
}

export interface UserUpdate {
  full_name?: string | null
}

export interface ResumePublic {
  id: number
  candidate_id: number
  file_name: string
  mime_type: string | null
  ingested: boolean
  parsed: Record<string, unknown> | null
}

export interface JDPublic {
  id: number
  recruiter_id: number
  title: string
  company: string | null
  seniority: string | null
  raw_text: string
  parsed_skills: Record<string, unknown> | null
  ingested: boolean
}

export interface JDCreate {
  title: string
  raw_text: string
  company?: string | null
  seniority?: string | null
}

export interface InterviewPublic {
  id: number
  candidate_id: number
  jd_id: number
  resume_id: number | null
  status: InterviewStatus
  livekit_room: string | null
  duration_minutes: number
  started_at: string | null
  ended_at: string | null
}

export interface InterviewSelfCreate {
  resume_id?: number
  duration_minutes?: number
}

export interface InterviewCreate {
  candidate_id: number
  jd_id: number
  resume_id?: number | null
  duration_minutes?: number
  config?: Record<string, unknown> | null
}

export interface LiveKitTokenResponse {
  url: string
  room: string
  identity: string
  token: string
}

export interface TurnPublic {
  idx: number
  skill_tag: string | null
  question: string
  answer_text: string | null
  score: Record<string, unknown> | null
  started_at: string | null
  answered_at: string | null
}

export interface ReportPublic {
  interview_id: number
  summary: string
  strengths: string | null
  weaknesses: string | null
  scores: Record<string, unknown>
  recommendation: string
  overall_score: number
  generated_at: string
}

export interface ProctorEventPublic {
  id: number
  interview_id: number
  kind: string
  severity: string
  ts: string
  payload: Record<string, unknown> | null
}

export interface ProctorEventIngest {
  kind?: string
  severity?: string
  payload?: Record<string, unknown> | null
}

export interface ResumeAnalyzeResponse {
  id: number
  file_name: string
  ingested: boolean
  parsed: Record<string, unknown>
  message: string
}

export type ResumeAnalysisEventType =
  | 'stage'
  | 'log'
  | 'progress'
  | 'result'
  | 'error'

export interface ResumeAnalysisEvent {
  type: ResumeAnalysisEventType | string
  step: string
  message: string
  progress: number
  status: 'pending' | 'running' | 'done' | 'error'
  detail?: Record<string, unknown>
  ts?: string
}

export interface WsEnvelope {
  channel?: string
  data?: {
    role?: string
    content?: string
    kind?: string
    severity?: string
    [key: string]: unknown
  }
}
