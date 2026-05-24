import type { ReactNode } from 'react'

interface PageHeaderProps {
  title: string
  subtitle?: string
  extra?: ReactNode
  size?: 'default' | 'large'
}

export function PageHeader({
  title,
  subtitle,
  extra,
  size = 'default',
}: PageHeaderProps) {
  return (
    <div className="mb-6 flex flex-col gap-4 sm:mb-8 md:flex-row md:items-end md:justify-between">
      <div className="min-w-0 flex-1">
        <h1
          className={`text-balance font-semibold tracking-tight text-white ${
            size === 'large'
              ? 'text-2xl sm:text-3xl lg:text-4xl'
              : 'text-xl sm:text-2xl lg:text-3xl'
          }`}
        >
          {title}
        </h1>
        {subtitle ? (
          <p className="mt-1.5 max-w-2xl text-sm leading-relaxed text-slate-400 sm:mt-2 sm:text-base">
            {subtitle}
          </p>
        ) : null}
      </div>
      {extra ? (
        <div className="flex w-full shrink-0 flex-wrap items-center gap-2 sm:w-auto sm:justify-end md:gap-3">
          {extra}
        </div>
      ) : null}
    </div>
  )
}
