import { createSlice, type PayloadAction } from '@reduxjs/toolkit'

import type {
  OtpChallengeResponse,
  SignupRequest,
  TokenResponse,
  UserPublic,
} from '@/types/api'

export interface AuthState {
  isAuthenticated: boolean
  isBootstrapping: boolean
  user: UserPublic | null
  tokenMeta: Pick<TokenResponse, 'user_id' | 'role'> | null
  otpChallenge: OtpChallengeResponse | null
  pendingEmail: string | null
  loading: boolean
  error: string | null
}

const initialState: AuthState = {
  isAuthenticated: false,
  isBootstrapping: true,
  user: null,
  tokenMeta: null,
  otpChallenge: null,
  pendingEmail: null,
  loading: false,
  error: null,
}

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    bootstrapStart(state) {
      state.isBootstrapping = true
    },
    bootstrapSuccess(state, action: PayloadAction<UserPublic | null>) {
      state.isBootstrapping = false
      state.user = action.payload
      state.isAuthenticated = Boolean(action.payload)
    },
    loginRequest(
      state,
      action: PayloadAction<{ email: string; password: string; otp_code?: string }>,
    ) {
      state.loading = true
      state.error = null
      state.pendingEmail = action.payload.email
    },
    loginSuccess(state, action: PayloadAction<{ user: UserPublic; tokenMeta: AuthState['tokenMeta'] }>) {
      state.loading = false
      state.isAuthenticated = true
      state.user = action.payload.user
      state.tokenMeta = action.payload.tokenMeta
      state.otpChallenge = null
      state.pendingEmail = null
      state.error = null
    },
    loginOtpRequired(state, action: PayloadAction<OtpChallengeResponse>) {
      state.loading = false
      state.otpChallenge = action.payload
      state.error = null
    },
    loginFailure(state, action: PayloadAction<string>) {
      state.loading = false
      state.error = action.payload
    },
    signupRequest(state, _action: PayloadAction<SignupRequest>) {
      state.loading = true
      state.error = null
    },
    signupSuccess(state, action: PayloadAction<{ user: UserPublic; tokenMeta: AuthState['tokenMeta'] }>) {
      state.loading = false
      state.isAuthenticated = true
      state.user = action.payload.user
      state.tokenMeta = action.payload.tokenMeta
      state.error = null
    },
    signupFailure(state, action: PayloadAction<string>) {
      state.loading = false
      state.error = action.payload
    },
    logout(state) {
      state.isBootstrapping = false
      state.isAuthenticated = false
      state.user = null
      state.tokenMeta = null
      state.otpChallenge = null
      state.pendingEmail = null
      state.loading = false
      state.error = null
    },
    clearAuthError(state) {
      state.error = null
    },
  },
})

export const authActions = authSlice.actions
export const authReducer = authSlice.reducer
