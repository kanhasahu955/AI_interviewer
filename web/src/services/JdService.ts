import { BaseService } from '@/services/BaseService'
import type { JDCreate, JDPublic } from '@/types/api'

export class JdService extends BaseService {
  list(): Promise<JDPublic[]> {
    return this.api.get<JDPublic[]>('/jds')
  }

  getById(id: number): Promise<JDPublic> {
    return this.api.get<JDPublic>(`/jds/${id}`)
  }

  create(payload: JDCreate): Promise<JDPublic> {
    return this.api.post<JDPublic>('/jds', payload)
  }
}

export const jdService = new JdService()
