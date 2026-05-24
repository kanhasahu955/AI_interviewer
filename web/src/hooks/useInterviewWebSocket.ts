import { useEffect, useRef } from 'react'

import { useAppDispatch, useAppSelector } from '@/app/hooks'
import { env } from '@/core/config/env'
import { TokenStorage } from '@/core/http/TokenStorage'
import { WebSocketClient } from '@/core/websocket/WebSocketClient'
import { interviewsActions } from '@/features/interviews/interviewsSlice'
import type { WsEnvelope } from '@/types/api'

export function useInterviewWebSocket(interviewId: number | null) {
  const dispatch = useAppDispatch()
  const isAuthenticated = useAppSelector((state) => state.auth.isAuthenticated)
  const clientRef = useRef<WebSocketClient | null>(null)

  useEffect(() => {
    if (!interviewId || !isAuthenticated) return

    const token = TokenStorage.getInstance().get()
    if (!token) return

    const url = `${env.wsBaseUrl}/ws/interviews/${interviewId}?token=${encodeURIComponent(token)}`
    const client = new WebSocketClient({
      url,
      reconnect: true,
      maxRetries: 4,
      retryDelayMs: 2000,
    })
    clientRef.current = client

    const offStatus = client.onStatus((status) => {
      dispatch(interviewsActions.setWsStatus(status))
    })

    const offMessage = client.onMessage((payload) => {
      dispatch(interviewsActions.processWsEnvelope(payload as WsEnvelope))
    })

    client.connect()

    return () => {
      offStatus()
      offMessage()
      client.disconnect()
      clientRef.current = null
      dispatch(interviewsActions.clearLiveSession())
    }
  }, [dispatch, interviewId, isAuthenticated])
}
