import { cn } from '@/lib/utils'
import { type InputHTMLAttributes, forwardRef } from 'react'

export type CheckboxProps = InputHTMLAttributes<HTMLInputElement>

export const Checkbox = forwardRef<HTMLInputElement, CheckboxProps>(
  ({ className, ...props }, ref) => (
    <input
      type="checkbox"
      ref={ref}
      className={cn(
        'h-4 w-4 rounded border border-border bg-surface cursor-pointer',
        '[accent-color:var(--color-primary)]',
        'focus:outline-none focus:ring-2 focus:ring-primary/25',
        'disabled:cursor-not-allowed disabled:opacity-50',
        className
      )}
      {...props}
    />
  )
)
Checkbox.displayName = 'Checkbox'
