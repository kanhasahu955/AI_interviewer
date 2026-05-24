import type { ApiErrorPayload } from '@/types/api'

export class ApiError extends Error {
  readonly status: number
  readonly code: string
  readonly details: unknown
  readonly requestId?: string

  constructor(
    message: string,
    options: {
      status?: number
      code?: string
      details?: unknown
      requestId?: string
    } = {},
  ) {
    super(message)
    this.name = 'ApiError'
    this.status = options.status ?? 500
    this.code = options.code ?? 'INTERNAL_ERROR'
    this.details = options.details
    this.requestId = options.requestId
  }

  static fromAxios(error: unknown): ApiError {
    if (error instanceof ApiError) return error

    const axiosError = error as {
      response?: { status?: number; data?: ApiErrorPayload }
      message?: string
    }

    const payload = axiosError.response?.data?.error
    if (payload) {
      return new ApiError(payload.message, {
        status: axiosError.response?.status,
        code: payload.code,
        details: payload.details,
        requestId: payload.request_id,
      })
    }

    return new ApiError(axiosError.message ?? 'Network error', {
      status: axiosError.response?.status ?? 0,
      code: 'NETWORK_ERROR',
    })
  }
}
