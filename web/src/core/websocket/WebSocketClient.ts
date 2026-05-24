export type WebSocketStatus = 'idle' | 'connecting' | 'open' | 'closed' | 'error'

export type WebSocketMessageHandler = (payload: unknown) => void
export type WebSocketStatusHandler = (status: WebSocketStatus) => void

export interface WebSocketClientOptions {
  url: string
  reconnect?: boolean
  maxRetries?: number
  retryDelayMs?: number
}

export class WebSocketClient {
  private socket: WebSocket | null = null
  private retries = 0
  private closedByUser = false
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null
  private readonly messageHandlers = new Set<WebSocketMessageHandler>()
  private readonly statusHandlers = new Set<WebSocketStatusHandler>()
  private readonly options: WebSocketClientOptions

  constructor(options: WebSocketClientOptions) {
    this.options = options
  }

  connect(): void {
    if (this.closedByUser) return

    this.clearReconnectTimer()
    this.setStatus('connecting')

    this.socket = new WebSocket(this.options.url)

    this.socket.onopen = () => {
      this.retries = 0
      this.setStatus('open')
    }

    this.socket.onmessage = (event) => {
      try {
        const payload = JSON.parse(String(event.data))
        this.messageHandlers.forEach((handler) => handler(payload))
      } catch {
        this.messageHandlers.forEach((handler) => handler(event.data))
      }
    }

    this.socket.onerror = () => {
      this.setStatus('error')
    }

    this.socket.onclose = () => {
      this.socket = null
      this.setStatus('closed')
      if (!this.closedByUser && this.options.reconnect !== false) {
        this.scheduleReconnect()
      }
    }
  }

  disconnect(): void {
    this.closedByUser = true
    this.clearReconnectTimer()
    this.socket?.close()
    this.socket = null
    this.setStatus('closed')
  }

  send(payload: unknown): void {
    if (this.socket?.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify(payload))
    }
  }

  onMessage(handler: WebSocketMessageHandler): () => void {
    this.messageHandlers.add(handler)
    return () => this.messageHandlers.delete(handler)
  }

  onStatus(handler: WebSocketStatusHandler): () => void {
    this.statusHandlers.add(handler)
    return () => this.statusHandlers.delete(handler)
  }

  private scheduleReconnect(): void {
    const maxRetries = this.options.maxRetries ?? 5
    if (this.retries >= maxRetries) return

    this.retries += 1
    const delay = (this.options.retryDelayMs ?? 1500) * this.retries
    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null
      this.connect()
    }, delay)
  }

  private clearReconnectTimer(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }
  }

  private setStatus(status: WebSocketStatus): void {
    this.statusHandlers.forEach((handler) => handler(status))
  }
}
