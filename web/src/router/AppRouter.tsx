import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'

import { ProtectedRoute } from '@/components/common/ProtectedRoute'
import { AppLayout } from '@/components/layout/AppLayout'
import {
  DashboardPage,
  InterviewCreatePage,
  InterviewDetailPage,
  InterviewListPage,
  InterviewRoomPage,
  JdsPage,
  LazyPage,
  LoginPage,
  NotFoundPage,
  ProfilePage,
  ReportPage,
  ResumesPage,
  SignupPage,
} from '@/router/lazyPages'

export function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        <Route
          path="/login"
          element={
            <LazyPage>
              <LoginPage />
            </LazyPage>
          }
        />
        <Route
          path="/signup"
          element={
            <LazyPage>
              <SignupPage />
            </LazyPage>
          }
        />

        <Route element={<ProtectedRoute />}>
          <Route element={<AppLayout />}>
            <Route index element={<Navigate to="/dashboard" replace />} />
            <Route
              path="/dashboard"
              element={
                <LazyPage>
                  <DashboardPage />
                </LazyPage>
              }
            />
            <Route
              path="/interviews"
              element={
                <LazyPage>
                  <InterviewListPage />
                </LazyPage>
              }
            />
            <Route
              path="/interviews/:id/room"
              element={
                <LazyPage>
                  <InterviewRoomPage />
                </LazyPage>
              }
            />
            <Route
              path="/interviews/:id"
              element={
                <LazyPage>
                  <InterviewDetailPage />
                </LazyPage>
              }
            />
            <Route
              element={<ProtectedRoute roles={['recruiter', 'admin']} />}
            >
              <Route
                path="/interviews/new"
                element={
                  <LazyPage>
                    <InterviewCreatePage />
                  </LazyPage>
                }
              />
              <Route
                path="/jds"
                element={
                  <LazyPage>
                    <JdsPage />
                  </LazyPage>
                }
              />
            </Route>
            <Route element={<ProtectedRoute roles={['candidate', 'admin']} />}>
              <Route
                path="/resumes"
                element={
                  <LazyPage>
                    <ResumesPage />
                  </LazyPage>
                }
              />
            </Route>
            <Route
              path="/reports/:id"
              element={
                <LazyPage>
                  <ReportPage />
                </LazyPage>
              }
            />
            <Route
              path="/profile"
              element={
                <LazyPage>
                  <ProfilePage />
                </LazyPage>
              }
            />
          </Route>
        </Route>

        <Route
          path="*"
          element={
            <LazyPage>
              <NotFoundPage />
            </LazyPage>
          }
        />
      </Routes>
    </BrowserRouter>
  )
}
