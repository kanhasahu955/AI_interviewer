import { BaseService } from '@/services/BaseService'
import type { ReportPublic } from '@/types/api'

export class ReportService extends BaseService {
  getByInterviewId(interviewId: number): Promise<ReportPublic> {
    return this.api.get<ReportPublic>(`/reports/${interviewId}`)
  }
}

export const reportService = new ReportService()
