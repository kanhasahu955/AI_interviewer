import { BaseService } from '@/services/BaseService'
import type { ProctorEventIngest, ProctorEventPublic } from '@/types/api'

export class ProctoringService extends BaseService {
  listEvents(interviewId: number): Promise<ProctorEventPublic[]> {
    return this.api.get<ProctorEventPublic[]>(`/proctoring/${interviewId}/events`)
  }

  ingestEvent(interviewId: number, payload: ProctorEventIngest): Promise<ProctorEventPublic> {
    return this.api.post<ProctorEventPublic>(
      `/proctoring/${interviewId}/events`,
      payload,
    )
  }
}

export const proctoringService = new ProctoringService()
