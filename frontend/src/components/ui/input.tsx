import { cn } from '@/lib/utils'
import { type InputHTMLAttributes, forwardRef } from 'react'

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  error?: boolean
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className, error, type, ...props }, ref) => (
    <input
      type={type}
      ref={ref}
      className={cn(
        'flex h-9 w-full rounded-md border bg-surface px-3 py-2 text-sm text-fg placeholder:text-fg-muted',
        'transition-colors duration-150',
        'focus:outline-none focus:ring-2 focus:ring-primary/25 focus:border-primary',
        'disabled:cursor-not-allowed disabled:opacity-50 disabled:bg-surface-raised',
        error
          ? 'border-danger focus:ring-danger/25 focus:border-danger'
          : 'border-border',
        className
      )}
      {...props}
    />
  )
)
Input.displayName = 'Input'
