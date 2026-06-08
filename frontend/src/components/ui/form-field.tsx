import { cn } from '@/lib/utils'
import { type HTMLAttributes, type ReactNode } from 'react'

export interface FormFieldProps extends HTMLAttributes<HTMLDivElement> {
  label?: string
  error?: string
  hint?: string
  required?: boolean
  htmlFor?: string
  children: ReactNode
}

export function FormField({
  className,
  label,
  error,
  hint,
  required,
  htmlFor,
  children,
  ...props
}: FormFieldProps) {
  return (
    <div className={cn('flex flex-col gap-1.5', className)} {...props}>
      {label && (
        <label
          htmlFor={htmlFor}
          className="text-sm font-medium text-fg leading-none"
        >
          {label}
          {required && (
            <span className="ml-0.5 text-danger" aria-hidden>
              *
            </span>
          )}
        </label>
      )}
      {children}
      {hint && !error && <p className="text-xs text-fg-muted">{hint}</p>}
      {error && <p className="text-xs text-danger" role="alert">{error}</p>}
    </div>
  )
}
