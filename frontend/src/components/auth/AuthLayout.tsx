import { type ReactNode } from 'react'
import { HubLogo } from './HubLogo'
import './auth.css'

interface AuthPanelProps {
  headline: ReactNode
  tagline: string
  badge?: ReactNode
  accentGradient?: string
}

interface AuthLayoutProps {
  panel: AuthPanelProps
  children: ReactNode
}

export function AuthLayout({ panel, children }: AuthLayoutProps) {
  return (
    <div className="min-h-screen flex">
      <aside className="hidden lg:flex lg:w-[42%] relative flex-col justify-between p-12 overflow-hidden bg-fg">
        <div className="absolute inset-0 auth-panel-grid" />
        {panel.accentGradient && (
          <div className="absolute inset-0" style={{ background: panel.accentGradient }} />
        )}

        <div className="relative z-10">
          <BrandMark variant="light" size="md" />
        </div>

        <div className="relative z-10 space-y-5">
          {panel.badge}
          <h2 className="text-[2.6rem] font-semibold font-display text-white leading-[1.15]">
            {panel.headline}
          </h2>
          <p className="text-sm leading-relaxed text-white/40">{panel.tagline}</p>
        </div>

        <div className="relative z-10">
          <p className="text-xs text-white/20">
            &copy; {new Date().getFullYear()} Agency Subscription Hub
          </p>
        </div>
      </aside>

      <div className="flex-1 flex items-center justify-center p-8 bg-bg">
        <div className="w-full max-w-[340px] animate-auth-fade-up">
          <div className="lg:hidden mb-10">
            <BrandMark variant="dark" size="sm" />
          </div>
          {children}
        </div>
      </div>
    </div>
  )
}

function BrandMark({
  variant,
  size,
}: {
  variant: 'light' | 'dark'
  size: 'sm' | 'md'
}) {
  return (
    <div className="flex items-center gap-2.5">
      <div
        className={`bg-primary flex items-center justify-center ${
          size === 'md' ? 'w-8 h-8 rounded-lg' : 'w-7 h-7 rounded-md'
        }`}
      >
        <HubLogo size={size === 'md' ? 16 : 14} />
      </div>
      <span
        className={`font-semibold text-sm tracking-wide font-display ${
          variant === 'light' ? 'text-white' : 'text-fg'
        }`}
      >
        Subscription Hub
      </span>
    </div>
  )
}
