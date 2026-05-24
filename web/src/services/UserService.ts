import { BaseService } from '@/services/BaseService'
import type { UserPublic, UserUpdate } from '@/types/api'

export class UserService extends BaseService {
  getMe(): Promise<UserPublic> {
    return this.api.get<UserPublic>('/users/me')
  }

  searchCandidates(query?: string): Promise<UserPublic[]> {
    return this.api.get<UserPublic[]>('/users/candidates', {
      params: query ? { q: query } : undefined,
    })
  }

  updateMe(payload: UserUpdate): Promise<UserPublic> {
    return this.api.patch<UserPublic>('/users/me', payload)
  }
}

export const userService = new UserService()
