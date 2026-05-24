import { useRoomContext } from '@livekit/components-react'
import { useEffect, useState } from 'react'

import { isAgentParticipant } from '@/components/interview/agentParticipant'

export interface VoiceVisemeState {
  level: number
  isSpeaking: boolean
}

const SILENT: VoiceVisemeState = {
  level: 0,
  isSpeaking: false,
}

function bandAvg(bins: Uint8Array, from: number, to: number): number {
  let sum = 0
  let count = 0
  for (let i = from; i < to && i < bins.length; i++) {
    sum += bins[i]
    count++
  }
  return count ? sum / count : 0
}

/** LiveKit agent audio → volume level for speaking indicator. */
export function useAgentAudioLevel(agentOnline: boolean): VoiceVisemeState {
  const room = useRoomContext()
  const [state, setState] = useState<VoiceVisemeState>(SILENT)

  useEffect(() => {
    if (!room || !agentOnline) {
      setState(SILENT)
      return
    }

    let audioCtx: AudioContext | null = null
    let analyser: AnalyserNode | null = null
    let raf = 0
    let disposed = false

    const attach = () => {
      const agent = [...room.remoteParticipants.values()].find((p) =>
        isAgentParticipant(p.identity, p.name),
      )
      const publication = agent
        ? [...agent.audioTrackPublications.values()].find((pub) => pub.track)
        : undefined
      const mediaTrack = publication?.track?.mediaStreamTrack
      if (!mediaTrack) return false

      audioCtx = new AudioContext()
      void audioCtx.resume()
      const stream = new MediaStream([mediaTrack])
      const source = audioCtx.createMediaStreamSource(stream)
      analyser = audioCtx.createAnalyser()
      analyser.fftSize = 1024
      analyser.smoothingTimeConstant = 0.55
      source.connect(analyser)

      const freq = new Uint8Array(analyser.frequencyBinCount)
      const time = new Uint8Array(analyser.fftSize)

      const tick = () => {
        if (!analyser || disposed) return
        analyser.getByteFrequencyData(freq)
        analyser.getByteTimeDomainData(time)

        let rms = 0
        for (let i = 0; i < time.length; i++) {
          const v = (time[i] - 128) / 128
          rms += v * v
        }
        rms = Math.sqrt(rms / time.length)

        const low = bandAvg(freq, 2, 24)

        const level = Math.min(1, rms * 4.2)
        const speaking = level > 0.04 || low > 18

        setState({
          level,
          isSpeaking: speaking,
        })
        raf = requestAnimationFrame(tick)
      }
      tick()
      return true
    }

    if (!attach()) {
      const retry = window.setInterval(() => {
        if (disposed || attach()) window.clearInterval(retry)
      }, 400)
      return () => {
        disposed = true
        window.clearInterval(retry)
        cancelAnimationFrame(raf)
        void audioCtx?.close()
      }
    }

    return () => {
      disposed = true
      cancelAnimationFrame(raf)
      void audioCtx?.close()
    }
  }, [room, agentOnline])

  return state
}
