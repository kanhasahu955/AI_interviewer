import { Alert, Button, Form, Input, Select, Typography } from 'antd'
import { useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { useAppDispatch, useAppSelector } from '@/app/hooks'
import { AuthLayout } from '@/components/layout/AuthLayout'
import { authActions } from '@/features/auth/authSlice'
import { authService } from '@/services/AuthService'

export function LoginPage() {
  const dispatch = useAppDispatch()
  const navigate = useNavigate()
  const { loading, error, otpChallenge, pendingEmail, isAuthenticated } =
    useAppSelector((state) => state.auth)
  const [form] = Form.useForm()

  useEffect(() => {
    if (isAuthenticated) navigate('/dashboard', { replace: true })
  }, [isAuthenticated, navigate])

  const onFinish = (values: {
    email: string
    password: string
    otp_code?: string
  }) => {
    dispatch(authActions.loginRequest(values))
  }

  const handleResendOtp = async () => {
    if (!pendingEmail) return
    try {
      await authService.requestOtp({ email: pendingEmail })
    } catch {
      /* message shown via form state */
    }
  }

  if (isAuthenticated) return null

  return (
    <AuthLayout
      title="Sign in"
      subtitle="Access your interviews, reports, and live dashboards."
    >
      {error ? (
        <Alert type="error" message={error} showIcon className="!mb-4" />
      ) : null}

      {otpChallenge ? (
        <Alert
          type="info"
          showIcon
          className="!mb-4"
          message={
            otpChallenge.delivery === 'email'
              ? `Code sent to ${otpChallenge.sent_to ?? 'your email'}`
              : 'Enter the code from your authenticator app'
          }
          description={otpChallenge.message}
        />
      ) : null}

      <Form
        form={form}
        layout="vertical"
        requiredMark={false}
        onFinish={onFinish}
        initialValues={{ email: pendingEmail ?? '' }}
        size="large"
      >
        <Form.Item
          label={<span className="text-slate-300">Email</span>}
          name="email"
          rules={[{ required: true, type: 'email' }]}
        >
          <Input placeholder="you@company.com" />
        </Form.Item>
        <Form.Item
          label={<span className="text-slate-300">Password</span>}
          name="password"
          rules={[{ required: true, min: 8 }]}
        >
          <Input.Password placeholder="••••••••" />
        </Form.Item>

        {otpChallenge ? (
          <Form.Item
            label={<span className="text-slate-300">Verification code</span>}
            name="otp_code"
            rules={[{ required: true, len: 6 }]}
          >
            <Input placeholder="123456" maxLength={6} />
          </Form.Item>
        ) : null}

        <Button type="primary" htmlType="submit" block loading={loading} className="!mt-2 !h-12">
          {otpChallenge ? 'Verify & sign in' : 'Sign in'}
        </Button>

        {otpChallenge?.delivery === 'email' ? (
          <Button type="link" block onClick={handleResendOtp} className="!text-indigo-400">
            Resend code
          </Button>
        ) : null}
      </Form>

      <Typography.Paragraph className="!mt-6 !mb-0 text-center !text-slate-400">
        New here?{' '}
        <Link to="/signup" className="font-medium text-indigo-400 hover:text-indigo-300">
          Create an account
        </Link>
      </Typography.Paragraph>
    </AuthLayout>
  )
}

export function SignupPage() {
  const dispatch = useAppDispatch()
  const navigate = useNavigate()
  const { loading, error, isAuthenticated } = useAppSelector(
    (state) => state.auth,
  )

  useEffect(() => {
    if (isAuthenticated) navigate('/dashboard', { replace: true })
  }, [isAuthenticated, navigate])

  if (isAuthenticated) return null

  return (
    <AuthLayout
      title="Create account"
      subtitle="Join as a candidate or recruiter to get started."
    >
      {error ? (
        <Alert type="error" message={error} showIcon className="!mb-4" />
      ) : null}

      <Form
        layout="vertical"
        requiredMark={false}
        onFinish={(values) => dispatch(authActions.signupRequest(values))}
        size="large"
      >
        <Form.Item label={<span className="text-slate-300">Full name</span>} name="full_name">
          <Input placeholder="Jane Doe" />
        </Form.Item>
        <Form.Item
          label={<span className="text-slate-300">Email</span>}
          name="email"
          rules={[{ required: true, type: 'email' }]}
        >
          <Input placeholder="you@company.com" />
        </Form.Item>
        <Form.Item
          label={<span className="text-slate-300">Password</span>}
          name="password"
          rules={[{ required: true, min: 8 }]}
        >
          <Input.Password placeholder="At least 8 characters" />
        </Form.Item>
        <Form.Item
          label={<span className="text-slate-300">Role</span>}
          name="role"
          initialValue="candidate"
          rules={[{ required: true }]}
        >
          <Select
            options={[
              { value: 'candidate', label: 'Candidate' },
              { value: 'recruiter', label: 'Recruiter' },
            ]}
          />
        </Form.Item>
        <Button type="primary" htmlType="submit" block loading={loading} className="!h-12">
          Create account
        </Button>
      </Form>

      <Typography.Paragraph className="!mt-6 !mb-0 text-center !text-slate-400">
        Already have an account?{' '}
        <Link to="/login" className="font-medium text-indigo-400 hover:text-indigo-300">
          Sign in
        </Link>
      </Typography.Paragraph>
    </AuthLayout>
  )
}
