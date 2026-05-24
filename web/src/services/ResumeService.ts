import { BaseService } from '@/services/BaseService'
import {
  streamResumeAnalysis,
  type ResumeAnalysisStreamHandlers,
} from '@/core/streaming/resumeAnalysisStream'
import type { ResumeAnalyzeResponse, ResumePublic } from '@/types/api'

export class ResumeService extends BaseService {
  list(candidateId?: number): Promise<ResumePublic[]> {
    return this.api.get<ResumePublic[]>('/resumes', {
      params: candidateId ? { candidate_id: candidateId } : undefined,
    })
  }

  getById(id: number): Promise<ResumePublic> {
    return this.api.get<ResumePublic>(`/resumes/${id}`)
  }

  upload(file: File): Promise<ResumePublic> {
    const form = new FormData()
    form.append('file', file)
    return this.api.postForm<ResumePublic>('/resumes', form)
  }

  analyze(id: number): Promise<ResumeAnalyzeResponse> {
    return this.api.post<ResumeAnalyzeResponse>(`/resumes/${id}/analyze`)
  }

  analyzeStream(
    id: number,
    handlers: ResumeAnalysisStreamHandlers,
  ): Promise<ResumeAnalyzeResponse> {
    return streamResumeAnalysis(id, handlers)
  }
}

export const resumeService = new ResumeService()
