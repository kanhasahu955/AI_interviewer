import type { ReactNode } from 'react'

interface PageContainerProps {
  children: ReactNode
  className?: string
}

export function PageContainer({ children, className = '' }: PageContainerProps) {
  return (
    <div className={`page-enter mx-auto w-full max-w-[1400px] ${className}`}>
      {children}
    </div>
  )
}
