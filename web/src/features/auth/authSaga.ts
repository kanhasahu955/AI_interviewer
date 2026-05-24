import { call, put, takeLatest } from 'redux-saga/effects'

import { authActions } from '@/features/auth/authSlice'
import { LOGOUT_ACTION } from '@/features/auth/session'
import { userActions } from '@/features/user/userSlice'
import { ApiError } from '@/core/errors/ApiError'
import { TokenStorage } from '@/core/http/TokenStorage'
import { authService } from '@/services/AuthService'
import { userService } from '@/services/UserService'
import type { UserPublic } from '@/types/api'

function* fetchUserAfterAuth(tokenMeta: { user_id: number; role: UserPublic['role'] }) {
  const user: UserPublic = yield call([userService, userService.getMe])
  yield put(authActions.loginSuccess({ user, tokenMeta }))
  yield put(userActions.setProfile(user))
}

function* handleLogin(
  action: ReturnType<typeof authActions.loginRequest>,
): Generator {
  try {
    const result = yield call([authService, authService.login], action.payload)

    if (result.kind === 'otp') {
      yield put(authActions.loginOtpRequired(result.challenge))
      return
    }

    yield* fetchUserAfterAuth({
      user_id: result.token!.user_id,
      role: result.token!.role,
    })
  } catch (error) {
    const message =
      error instanceof ApiError ? error.message : 'Login failed'
    yield put(authActions.loginFailure(message))
  }
}

function* handleSignup(
  action: ReturnType<typeof authActions.signupRequest>,
): Generator {
  try {
    const token = yield call([authService, authService.signup], action.payload)
    yield* fetchUserAfterAuth({ user_id: token.user_id, role: token.role })
  } catch (error) {
    const message =
      error instanceof ApiError ? error.message : 'Signup failed'
    yield put(authActions.signupFailure(message))
  }
}

function* handleBootstrap(): Generator {
  yield put(authActions.bootstrapStart())
  const token = TokenStorage.getInstance().get()

  if (!token) {
    yield put(authActions.bootstrapSuccess(null))
    return
  }

  try {
    const user: UserPublic = yield call([userService, userService.getMe])
    yield put(authActions.bootstrapSuccess(user))
    yield put(userActions.setProfile(user))
  } catch {
    authService.logout()
    yield put(authActions.bootstrapSuccess(null))
  }
}

export function* authSaga(): Generator {
  yield takeLatest(authActions.loginRequest.type, handleLogin)
  yield takeLatest(authActions.signupRequest.type, handleSignup)
  yield takeLatest('auth/bootstrap', handleBootstrap)
  yield takeLatest(LOGOUT_ACTION, function* noop() {
    /* session cleared synchronously via logoutSession() */
  })
}
