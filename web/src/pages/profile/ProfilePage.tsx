import { SafetyCertificateOutlined, UserOutlined } from '@ant-design/icons'
import { Alert, Avatar, Button, Form, Input, Typography, message } from 'antd'
import { useState } from 'react'

import { useAppDispatch, useAppSelector } from '@/app/hooks'
import { PageContainer } from '@/components/common/PageContainer'
import { PageHeader } from '@/components/common/PageHeader'
import { SectionCard } from '@/components/common/SectionCard'
import { userActions } from '@/features/user/userSlice'
import { authService } from '@/services/AuthService'

export function ProfilePage() {
  const dispatch = useAppDispatch()
  const user = useAppSelector((state) => state.user.profile ?? state.auth.user)
  const { updating, error } = useAppSelector((state) => state.user)
  const [otpInfo, setOtpInfo] = useState<string | null>(null)
  const [verifyCode, setVerifyCode] = useState('')

  const handleEnrolOtp = async () => {
    try {
      const res = await authService.enrolOtp()
      setOtpInfo(res.message + (res.secret ? ` Secret: ${res.secret}` : ''))
      message.success('OTP enrolment started')
    } catch {
      message.error('Could not start OTP enrolment')
    }
  }

  const handleVerifyOtp = async () => {
    try {
      await authService.verifyOtp({ code: verifyCode })
      message.success('Two-factor authentication enabled')
      setOtpInfo(null)
      setVerifyCode('')
    } catch {
      message.error('Invalid verification code')
    }
  }

  return (
    <PageContainer>
      <PageHeader
        title="Profile"
        subtitle="Manage your account details and security settings."
      />

      {error ? <Alert type="error" message={error} showIcon className="mb-4" /> : null}

      <div className="grid gap-6 lg:grid-cols-2">
        <SectionCard title="Account">
          <div className="mb-6 flex items-center gap-4">
            <Avatar
              size={64}
              icon={<UserOutlined />}
              className="!bg-gradient-to-br !from-indigo-500 !to-violet-600"
            >
              {(user?.full_name ?? user?.email ?? '?').slice(0, 1).toUpperCase()}
            </Avatar>
            <div className="min-w-0">
              <p className="truncate font-semibold text-white">
                {user?.full_name ?? 'Unnamed user'}
              </p>
              <p className="truncate text-sm text-slate-400">{user?.email}</p>
              <span className="mt-1 inline-block rounded-full bg-white/5 px-2.5 py-0.5 text-xs capitalize text-slate-400">
                {user?.role}
              </span>
            </div>
          </div>

          <Form
            layout="vertical"
            initialValues={{ full_name: user?.full_name ?? '' }}
            onFinish={(values) =>
              dispatch(userActions.updateProfileRequest(values))
            }
          >
            <Form.Item label="Email">
              <Input value={user?.email} disabled size="large" />
            </Form.Item>
            <Form.Item label="Full name" name="full_name">
              <Input placeholder="Your name" size="large" />
            </Form.Item>
            <Button type="primary" htmlType="submit" loading={updating} size="large">
              Save changes
            </Button>
          </Form>
        </SectionCard>

        <SectionCard title="Security">
          <div className="mb-4 flex items-center gap-3 text-slate-400">
            <SafetyCertificateOutlined className="text-lg text-indigo-400" />
            <Typography.Paragraph className="!mb-0 !text-sm sm:!text-base">
              {user?.otp_enabled
                ? 'Two-factor authentication is enabled on your account.'
                : 'Add an extra layer of security to your login flow.'}
            </Typography.Paragraph>
          </div>

          {user?.otp_enabled ? (
            <div className="rounded-xl bg-emerald-500/10 px-4 py-3 text-sm text-emerald-300">
              ✓ OTP protection active
            </div>
          ) : (
            <>
              <Button onClick={handleEnrolOtp} size="large" block className="sm:!w-auto">
                Enrol OTP
              </Button>
              {otpInfo ? (
                <div className="mt-4 space-y-3">
                  <Alert type="info" message={otpInfo} />
                  <Input
                    size="large"
                    placeholder="Enter verification code"
                    value={verifyCode}
                    onChange={(e) => setVerifyCode(e.target.value)}
                  />
                  <Button type="primary" onClick={handleVerifyOtp} size="large" block className="sm:!w-auto">
                    Verify & enable
                  </Button>
                </div>
              ) : null}
            </>
          )}
        </SectionCard>
      </div>
    </PageContainer>
  )
}
