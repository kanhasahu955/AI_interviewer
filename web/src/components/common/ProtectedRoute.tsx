import { Navigate, Outlet, useLocation } from 'react-router-dom'

import { useAppSelector } from '@/app/hooks'
import { LoadingScreen } from '@/components/common/LoadingScreen'
import type { UserRole } from '@/types/api'

interface ProtectedRouteProps {
  roles?: UserRole[]
}

export function ProtectedRoute({ roles }: ProtectedRouteProps) {
  const location = useLocation()
  const { isAuthenticated, isBootstrapping, user } = useAppSelector(
    (state) => state.auth,
  )

  if (isBootstrapping) {
    return <LoadingScreen label="Starting session…" />
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />
  }

  if (roles && user && !roles.includes(user.role)) {
    return <Navigate to="/dashboard" replace />
  }

  return <Outlet />
}
