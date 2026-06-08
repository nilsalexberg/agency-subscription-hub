import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '@/lib/utils'
import { type HTMLAttributes } from 'react'
import { AlertCircle, CheckCircle2, Info, AlertTriangle } from 'lucide-react'

const alertVariants = cva(
  'relative flex gap-3 rounded-lg border p-4 text-sm',
  {
    variants: {
      variant: {
        default: 'border-border bg-surface-raised text-fg',
        info: 'border-info/20 bg-info-light text-info',
        success: 'border-success/20 bg-success-light text-success',
        warning: 'border-warning/20 bg-warning-light text-warning',
        danger: 'border-danger/20 bg-danger-light text-danger',
      },
    },
    defaultVariants: {
      variant: 'default',
    },
  }
)

const ICONS = {
  default: AlertCircle,
  info: Info,
  success: CheckCircle2,
  warning: AlertTriangle,
  danger: AlertCircle,
} as const

export interface AlertProps
  extends HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof alertVariants> {
  title?: string
}

export function Alert({
  className,
  variant = 'default',
  title,
  children,
  ...props
}: AlertProps) {
  const Icon = ICONS[variant ?? 'default']
  return (
    <div className={cn(alertVariants({ variant }), className)} role="alert" {...props}>
      <Icon className="mt-0.5 size-4 shrink-0" />
      <div className="flex-1">
        {title && <p className="font-semibold mb-0.5">{title}</p>}
        <div className="text-sm opacity-90">{children}</div>
      </div>
    </div>
  )
}
