import { Component, type ErrorInfo, type ReactNode } from 'react'
import { Button, Result } from 'antd'

interface ErrorBoundaryProps {
  children: ReactNode
  fallbackTitle?: string
}

interface ErrorBoundaryState {
  hasError: boolean
  message: string
}

export class ErrorBoundary extends Component<
  ErrorBoundaryProps,
  ErrorBoundaryState
> {
  state: ErrorBoundaryState = { hasError: false, message: '' }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, message: error.message }
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    console.error('[ErrorBoundary]', error, info.componentStack)
  }

  private handleReset = (): void => {
    this.setState({ hasError: false, message: '' })
    window.location.assign('/')
  }

  render(): ReactNode {
    if (this.state.hasError) {
      return (
        <div className="flex min-h-screen items-center justify-center p-6">
          <Result
            status="error"
            title={this.props.fallbackTitle ?? 'Something went wrong'}
            subTitle={this.state.message || 'An unexpected error occurred.'}
            extra={
              <Button type="primary" onClick={this.handleReset}>
                Return home
              </Button>
            }
          />
        </div>
      )
    }

    return this.props.children
  }
}
