import { call, put, takeLatest } from 'redux-saga/effects'

import { userActions } from '@/features/user/userSlice'
import { authActions } from '@/features/auth/authSlice'
import { ApiError } from '@/core/errors/ApiError'
import { userService } from '@/services/UserService'
import type { UserPublic } from '@/types/api'

function* handleUpdateProfile(
  action: ReturnType<typeof userActions.updateProfileRequest>,
): Generator {
  try {
    const user: UserPublic = yield call(
      [userService, userService.updateMe],
      action.payload,
    )
    yield put(userActions.updateProfileSuccess(user))
    yield put(authActions.bootstrapSuccess(user))
  } catch (error) {
    const message =
      error instanceof ApiError ? error.message : 'Profile update failed'
    yield put(userActions.updateProfileFailure(message))
  }
}

export function* userSaga(): Generator {
  yield takeLatest(userActions.updateProfileRequest.type, handleUpdateProfile)
}
