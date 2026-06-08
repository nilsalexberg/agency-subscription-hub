import { cn } from '@/lib/utils'
import { type SelectHTMLAttributes, forwardRef } from 'react'
import { ChevronDown } from 'lucide-react'

export interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  error?: boolean
}

export const Select = forwardRef<HTMLSelectElement, SelectProps>(
  ({ className, error, children, ...props }, ref) => (
    <div className="relative">
      <select
        ref={ref}
        className={cn(
          'flex h-9 w-full appearance-none rounded-md border bg-surface px-3 py-2 pr-8 text-sm text-fg',
          'transition-colors duration-150 cursor-pointer',
          'focus:outline-none focus:ring-2 focus:ring-primary/25 focus:border-primary',
          'disabled:cursor-not-allowed disabled:opacity-50 disabled:bg-surface-raised',
          error
            ? 'border-danger focus:ring-danger/25 focus:border-danger'
            : 'border-border',
          className
        )}
        {...props}
      >
        {children}
      </select>
      <ChevronDown className="pointer-events-none absolute right-2.5 top-1/2 -translate-y-1/2 size-4 text-fg-muted" />
    </div>
  )
)
Select.displayName = 'Select'
