import { BaseService } from '@/services/BaseService'
import type {
  InterviewCreate,
  InterviewPublic,
  InterviewSelfCreate,
  LiveKitTokenResponse,
  TurnPublic,
} from '@/types/api'

export class InterviewService extends BaseService {
  list(): Promise<InterviewPublic[]> {
    return this.api.get<InterviewPublic[]>('/interviews')
  }

  getById(id: number): Promise<InterviewPublic> {
    return this.api.get<InterviewPublic>(`/interviews/${id}`)
  }

  create(payload: InterviewCreate): Promise<InterviewPublic> {
    return this.api.post<InterviewPublic>('/interviews', payload)
  }

  createSelf(payload: InterviewSelfCreate = {}): Promise<InterviewPublic> {
    return this.api.post<InterviewPublic>('/interviews/self', payload)
  }

  end(id: number): Promise<InterviewPublic> {
    return this.api.post<InterviewPublic>(`/interviews/${id}/end`)
  }

  getToken(id: number): Promise<LiveKitTokenResponse> {
    return this.api.post<LiveKitTokenResponse>(`/interviews/${id}/token`)
  }

  getTurns(id: number): Promise<TurnPublic[]> {
    return this.api.get<TurnPublic[]>(`/interviews/${id}/turns`)
  }
}

export const interviewService = new InterviewService()
