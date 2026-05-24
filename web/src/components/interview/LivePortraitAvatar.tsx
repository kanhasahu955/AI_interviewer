import { useEffect, useRef } from 'react'

import { env } from '@/core/config/env'

function resolveMediaUrl(path: string | null | undefined): string | null {
  if (!path) return null
  if (path.startsWith('http://') || path.startsWith('https://')) return path
  const base = env.apiBaseUrl.replace(/\/$/, '')
  return `${base}${path.startsWith('/') ? path : `/${path}`}`
}

interface InterviewerVideoTileProps {
  name: string
  stillSrc: string
  portraitVideoUrl?: string | null
  isSpeaking: boolean
  audioLevel: number
}

/** Interviewer video tile — static photo, pre-rendered clip, or LiveKit track (via parent). */
export function InterviewerVideoTile({
  name,
  stillSrc,
  portraitVideoUrl,
  isSpeaking,
  audioLevel,
}: InterviewerVideoTileProps) {
  const videoRef = useRef<HTMLVideoElement>(null)
  const resolvedVideo = resolveMediaUrl(portraitVideoUrl)
  const showClip = Boolean(resolvedVideo)

  useEffect(() => {
    const el = videoRef.current
    if (!el || !resolvedVideo) return
    el.src = resolvedVideo
    void el.play().catch(() => undefined)
  }, [resolvedVideo])

  return (
    <div className="relative h-full min-h-[240px] w-full overflow-hidden bg-slate-950">
      {showClip ? (
        <video
          ref={videoRef}
          className="absolute inset-0 h-full w-full object-cover object-[center_18%]"
          playsInline
          muted
          loop={false}
          poster={stillSrc}
        />
      ) : (
        <img
          src={stillSrc}
          alt={`${name}, interviewer`}
          className={`absolute inset-0 h-full w-full object-cover object-[center_18%] transition-[filter,transform] duration-300 ${
            isSpeaking ? 'scale-[1.015] brightness-105' : 'scale-100 brightness-100'
          }`}
          draggable={false}
        />
      )}

      <div className="pointer-events-none absolute inset-0 bg-gradient-to-t from-black/50 via-transparent to-black/15" />

      {isSpeaking ? (
        <div className="absolute bottom-14 right-3 z-10 flex items-end gap-0.5 rounded-md bg-black/45 px-2 py-1.5 backdrop-blur-sm">
          {[0, 1, 2, 3].map((i) => (
            <span
              key={i}
              className="w-0.5 animate-pulse rounded-full bg-emerald-400"
              style={{
                height: `${6 + audioLevel * (14 + (i % 2) * 6)}px`,
                opacity: 0.5 + audioLevel * 0.5,
                animationDelay: `${i * 80}ms`,
              }}
            />
          ))}
        </div>
      ) : null}
    </div>
  )
}
