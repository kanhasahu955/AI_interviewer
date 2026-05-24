import { Suspense, lazy, type ComponentType, type ReactNode } from 'react'

import { LoadingScreen } from '@/components/common/LoadingScreen'

function lazyNamed<T extends ComponentType<object>>(
  factory: () => Promise<Record<string, T>>,
  exportName: string,
) {
  return lazy(async () => {
    const module = await factory()
    const component = module[exportName]
    if (!component) {
      throw new Error(`Missing export "${exportName}"`)
    }
    return { default: component }
  })
}

function LazyPage({ children }: { children: ReactNode }) {
  return <Suspense fallback={<LoadingScreen />}>{children}</Suspense>
}

export const LoginPage = lazyNamed(
  () => import('@/pages/auth/AuthPages'),
  'LoginPage',
)
export const SignupPage = lazyNamed(
  () => import('@/pages/auth/AuthPages'),
  'SignupPage',
)
export const DashboardPage = lazyNamed(
  () => import('@/pages/dashboard/DashboardPage'),
  'DashboardPage',
)
export const InterviewListPage = lazyNamed(
  () => import('@/pages/interviews/InterviewListPage'),
  'InterviewListPage',
)
export const InterviewDetailPage = lazyNamed(
  () => import('@/pages/interviews/InterviewDetailPage'),
  'InterviewDetailPage',
)
export const InterviewCreatePage = lazyNamed(
  () => import('@/pages/interviews/InterviewCreatePage'),
  'InterviewCreatePage',
)
export const InterviewRoomPage = lazyNamed(
  () => import('@/pages/interviews/InterviewRoomPage'),
  'InterviewRoomPage',
)
export const JdsPage = lazyNamed(() => import('@/pages/jds/JdsPage'), 'JdsPage')
export const ResumesPage = lazyNamed(
  () => import('@/pages/resumes/ResumesPage'),
  'ResumesPage',
)
export const ReportPage = lazyNamed(
  () => import('@/pages/reports/ReportPage'),
  'ReportPage',
)
export const ProfilePage = lazyNamed(
  () => import('@/pages/profile/ProfilePage'),
  'ProfilePage',
)
export const NotFoundPage = lazyNamed(
  () => import('@/pages/NotFoundPage'),
  'NotFoundPage',
)

export { LazyPage }
