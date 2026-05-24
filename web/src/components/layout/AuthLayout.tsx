import type { ReactNode } from 'react'

interface AuthLayoutProps {
  title: string
  subtitle: string
  children: ReactNode
}

const FEATURES = [
  'LiveKit voice & video interviews',
  'AI multi-agent evaluation',
  'Resume-aware questioning',
  'Real-time proctoring insights',
]

export function AuthLayout({ title, subtitle, children }: AuthLayoutProps) {
  return (
    <div className="relative min-h-screen overflow-hidden">
      <div className="pointer-events-none absolute inset-0 mesh-bg" />

      <div className="relative grid min-h-screen lg:grid-cols-2">
        <section className="relative hidden flex-col justify-between overflow-hidden p-10 xl:p-14 lg:flex">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_20%_20%,rgba(99,102,241,0.25),transparent_50%),radial-gradient(circle_at_80%_80%,rgba(168,85,247,0.15),transparent_45%)]" />

          <div className="relative z-10">
            <div className="mb-8 inline-flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-indigo-500 to-violet-600 text-lg font-bold text-white shadow-xl shadow-indigo-500/30">
              IA
            </div>
            <h1 className="text-balance text-4xl font-bold leading-tight text-white xl:text-5xl">
              Hire smarter with
              <span className="gradient-text"> AI interviews</span>
            </h1>
            <p className="mt-5 max-w-md text-base leading-relaxed text-slate-300">
              Real-time voice interviews, intelligent evaluation, and
              role-based dashboards — built for modern hiring teams.
            </p>

            <ul className="mt-10 space-y-3">
              {FEATURES.map((feature) => (
                <li
                  key={feature}
                  className="flex items-center gap-3 text-sm text-slate-300"
                >
                  <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-indigo-500/20 text-xs text-indigo-300">
                    ✓
                  </span>
                  {feature}
                </li>
              ))}
            </ul>
          </div>

          <p className="relative z-10 text-sm text-slate-500">
            Secure · Observable · Enterprise-ready
          </p>
        </section>

        <section className="flex min-h-screen flex-col justify-center px-4 py-8 sm:px-8 sm:py-12 lg:px-12">
          <div className="mb-6 flex items-center gap-3 lg:hidden">
            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 to-violet-600 text-sm font-bold text-white">
              IA
            </div>
            <div>
              <p className="font-semibold text-white">Interviewer AI</p>
              <p className="text-xs text-slate-500">Smart hiring platform</p>
            </div>
          </div>

          <div className="glass-panel mx-auto w-full max-w-md p-6 sm:p-8">
            <div className="mb-6 sm:mb-8">
              <h2 className="text-2xl font-bold text-white sm:text-3xl">{title}</h2>
              <p className="mt-2 text-sm leading-relaxed text-slate-400 sm:text-base">
                {subtitle}
              </p>
            </div>
            {children}
          </div>
        </section>
      </div>
    </div>
  )
}
