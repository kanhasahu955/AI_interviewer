import { Spin } from 'antd'

interface LoadingScreenProps {
  label?: string
  fullPage?: boolean
}

export function LoadingScreen({
  label = 'Loading…',
  fullPage = false,
}: LoadingScreenProps) {
  return (
    <div
      className={`flex flex-col items-center justify-center gap-4 ${
        fullPage ? 'min-h-[60vh]' : 'min-h-[200px] py-12'
      }`}
    >
      <Spin size="large" />
      <p className="text-sm text-slate-400">{label}</p>
    </div>
  )
}
