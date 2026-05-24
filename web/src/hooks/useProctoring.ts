import { useEffect, useRef } from 'react'

import { proctoringService } from '@/services/ProctoringService'

/** Browser-side proctoring: tab blur, visibility change, offline. */
export function useProctoring(interviewId: number | null, enabled: boolean) {
  const lastTabBlur = useRef(0)

  useEffect(() => {
    if (!interviewId || !enabled) return

    const send = (kind: string, severity: string, payload?: Record<string, unknown>) => {
      proctoringService.ingestEvent(interviewId, { kind, severity, payload }).catch(() => {
        /* best-effort */
      })
    }

    const onVisibility = () => {
      if (document.hidden) {
        const now = Date.now()
        if (now - lastTabBlur.current < 5000) return
        lastTabBlur.current = now
        send('tab_blur', 'warn', { reason: 'document_hidden' })
      }
    }

    const onBlur = () => {
      const now = Date.now()
      if (now - lastTabBlur.current < 5000) return
      lastTabBlur.current = now
      send('tab_blur', 'info', { reason: 'window_blur' })
    }

    const onOffline = () => send('network_drop', 'warn', { online: false })
    const onOnline = () => send('network_drop', 'info', { online: true })

    document.addEventListener('visibilitychange', onVisibility)
    window.addEventListener('blur', onBlur)
    window.addEventListener('offline', onOffline)
    window.addEventListener('online', onOnline)

    return () => {
      document.removeEventListener('visibilitychange', onVisibility)
      window.removeEventListener('blur', onBlur)
      window.removeEventListener('offline', onOffline)
      window.removeEventListener('online', onOnline)
    }
  }, [interviewId, enabled])
}
