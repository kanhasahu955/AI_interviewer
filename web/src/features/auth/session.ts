import type { AppDispatch } from '@/app/store'
import { authActions } from '@/features/auth/authSlice'
import { interviewsActions } from '@/features/interviews/interviewsSlice'
import { userActions } from '@/features/user/userSlice'
import { authService } from '@/services/AuthService'

/** Clear token + Redux auth immediately (do not wait for saga). */
export function logoutSession(dispatch: AppDispatch): void {
  authService.logout()
  dispatch(authActions.logout())
  dispatch(userActions.clearProfile())
  dispatch(interviewsActions.resetSession())
}

export const LOGOUT_ACTION = 'auth/logout' as const
