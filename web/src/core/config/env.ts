export const env = {
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL ?? '',
  wsBaseUrl:
    import.meta.env.VITE_WS_BASE_URL ??
    (typeof window !== 'undefined'
      ? `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}`
      : 'ws://localhost:5173'),
} as const

export const API_PREFIX = '/api/v1'
