import { cn } from '@/lib/utils'
import { type TextareaHTMLAttributes, forwardRef } from 'react'

export interface TextareaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  error?: boolean
}

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, error, ...props }, ref) => (
    <textarea
      ref={ref}
      className={cn(
        'flex min-h-[80px] w-full rounded-md border bg-surface px-3 py-2 text-sm text-fg placeholder:text-fg-muted',
        'resize-y transition-colors duration-150',
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
Textarea.displayName = 'Textarea'
