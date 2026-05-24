import {
  AudioOutlined,
  SafetyCertificateOutlined,
  VideoCameraOutlined,
} from '@ant-design/icons'
import { Alert, Button, Checkbox, Typography } from 'antd'
import { useState } from 'react'

interface InterviewLobbyProps {
  loading?: boolean
  onJoin: () => void
}

export function InterviewLobby({ loading, onJoin }: InterviewLobbyProps) {
  const [cameraOk, setCameraOk] = useState(false)
  const [micOk, setMicOk] = useState(false)
  const [proctorOk, setProctorOk] = useState(false)

  const testDevices = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true })
      stream.getTracks().forEach((t) => t.stop())
      setCameraOk(true)
      setMicOk(true)
    } catch {
      setCameraOk(false)
      setMicOk(false)
    }
  }

  const canJoin = cameraOk && micOk && proctorOk

  return (
    <div className="surface-card p-5 sm:p-8">
      <div className="mb-6 grid gap-4 lg:grid-cols-[1fr,280px]">
        <div>
          <Typography.Title level={3} className="!mt-0 !text-white">
            Meet Alex — your interviewer
          </Typography.Title>
          <Typography.Paragraph className="!text-slate-400">
            You will join a split-screen live room: your camera on the left, Alex on the
            right. Alex reads your resume, asks questions by voice, and saves every answer
            to your profile.
          </Typography.Paragraph>
        </div>

        <div className="overflow-hidden rounded-2xl border border-white/10 bg-slate-900">
          <div className="relative aspect-[4/5] w-full">
            <img
              src="/avatars/alex.jpg"
              alt="Alex, interviewer"
              className="h-full w-full object-cover object-[center_18%]"
            />
            <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent" />
            <div className="absolute bottom-3 left-3">
              <p className="font-semibold text-white">Alex</p>
              <p className="text-xs text-white/70">Senior Technical Interviewer</p>
            </div>
          </div>
        </div>
      </div>

      <div className="my-6 grid gap-3 sm:grid-cols-3">
        <div className="rounded-xl bg-white/[0.04] p-4 text-center">
          <VideoCameraOutlined className="text-2xl text-indigo-400" />
          <p className="mt-2 text-sm text-slate-300">Your camera</p>
        </div>
        <div className="rounded-xl bg-white/[0.04] p-4 text-center">
          <AudioOutlined className="text-2xl text-indigo-400" />
          <p className="mt-2 text-sm text-slate-300">Speak answers aloud</p>
        </div>
        <div className="rounded-xl bg-white/[0.04] p-4 text-center">
          <SafetyCertificateOutlined className="text-2xl text-indigo-400" />
          <p className="mt-2 text-sm text-slate-300">Proctoring on</p>
        </div>
      </div>

      <Alert
        type="info"
        showIcon
        className="!mb-5"
        message="Before you join"
        description="Use Chrome or Edge in a quiet room. Backend must run with make dev (includes LiveKit agent worker)."
      />

      <div className="space-y-3">
        <Checkbox checked={cameraOk} onChange={(e) => setCameraOk(e.target.checked)}>
          Camera is working
        </Checkbox>
        <Checkbox checked={micOk} onChange={(e) => setMicOk(e.target.checked)}>
          Microphone is working
        </Checkbox>
        <Checkbox checked={proctorOk} onChange={(e) => setProctorOk(e.target.checked)}>
          I agree to proctoring (tab focus &amp; integrity monitoring)
        </Checkbox>
      </div>

      <div className="mt-6 flex flex-wrap gap-3">
        <Button onClick={testDevices}>Test camera &amp; mic</Button>
        <Button type="primary" size="large" disabled={!canJoin} loading={loading} onClick={onJoin}>
          Join Alex in the interview room
        </Button>
      </div>
    </div>
  )
}
