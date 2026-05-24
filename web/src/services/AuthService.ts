import type { AxiosResponse } from 'axios'

import { TokenStorage } from '@/core/http/TokenStorage'
import { BaseService } from '@/services/BaseService'
import type {
  LoginRequest,
  OtpChallengeResponse,
  OtpEnrolResponse,
  OtpRequestPayload,
  OtpVerifyRequest,
  SignupRequest,
  TokenResponse,
} from '@/types/api'

export interface LoginResult {
  kind: 'token' | 'otp'
  token?: TokenResponse
  challenge?: OtpChallengeResponse
}

export class AuthService extends BaseService {
  async signup(payload: SignupRequest): Promise<TokenResponse> {
    const token = await this.api.post<TokenResponse>('/auth/signup', payload)
    TokenStorage.getInstance().set(token.access_token)
    return token
  }

  async login(payload: LoginRequest): Promise<LoginResult> {
    const response: AxiosResponse<TokenResponse | OtpChallengeResponse> =
      await this.api.axios.post('/auth/login', payload)

    if (response.status === 202) {
      return { kind: 'otp', challenge: response.data as OtpChallengeResponse }
    }

    const token = response.data as TokenResponse
    TokenStorage.getInstance().set(token.access_token)
    return { kind: 'token', token }
  }

  async requestOtp(payload: OtpRequestPayload): Promise<OtpChallengeResponse> {
    return this.api.post<OtpChallengeResponse>('/auth/otp/request', payload)
  }

  async enrolOtp(): Promise<OtpEnrolResponse> {
    return this.api.post<OtpEnrolResponse>('/auth/otp/enrol')
  }

  async verifyOtp(payload: OtpVerifyRequest): Promise<{ otp_enabled: boolean }> {
    return this.api.post('/auth/otp/verify', payload)
  }

  logout(): void {
    TokenStorage.getInstance().clear()
  }
}

export const authService = new AuthService()
