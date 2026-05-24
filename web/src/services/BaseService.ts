import { ApiClient } from '@/core/http/ApiClient'

export abstract class BaseService {
  protected readonly api: ApiClient

  constructor(api: ApiClient = ApiClient.getInstance()) {
    this.api = api
  }
}
