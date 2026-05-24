import type { ReactNode } from 'react'

interface SectionCardProps {
  title?: ReactNode
  extra?: ReactNode
  children: ReactNode
  className?: string
  bodyClassName?: string
  noPadding?: boolean
}

export function SectionCard({
  title,
  extra,
  children,
  className = '',
  bodyClassName = '',
  noPadding = false,
}: SectionCardProps) {
  return (
    <section className={`surface-card overflow-hidden ${className}`}>
      {title || extra ? (
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-white/[0.06] px-4 py-3 sm:px-5 sm:py-4">
          {title ? (
            <h2 className="text-base font-semibold text-white sm:text-lg">{title}</h2>
          ) : (
            <span />
          )}
          {extra}
        </div>
      ) : null}
      <div className={noPadding ? bodyClassName : `p-4 sm:p-5 ${bodyClassName}`}>
        {children}
      </div>
    </section>
  )
}
