import { App as AntApp, ConfigProvider } from 'antd'
import { useEffect, type ReactNode } from 'react'
import { Provider } from 'react-redux'

import { store } from '@/app/store'
import { ApiClient } from '@/core/http/ApiClient'
import { ErrorBoundary } from '@/components/common/ErrorBoundary'
import { logoutSession } from '@/features/auth/session'
import { antdTheme } from '@/theme/antdTheme'

interface AppProvidersProps {
  children: ReactNode
}

export function AppProviders({ children }: AppProvidersProps) {
  useEffect(() => {
    ApiClient.getInstance().onUnauthorized(() => {
      logoutSession(store.dispatch)
    })
    store.dispatch({ type: 'auth/bootstrap' })
  }, [])

  return (
    <Provider store={store}>
      <ConfigProvider theme={antdTheme}>
        <AntApp>
          <ErrorBoundary>{children}</ErrorBoundary>
        </AntApp>
      </ConfigProvider>
    </Provider>
  )
}
