import { useState, useRef } from 'react'
import { MoreHorizontal } from 'lucide-react'
import type { ResourceConfig } from '@/types/resource'
import { Button } from '@/components/ui'
import { useClickOutside } from '@/hooks/useClickOutside'

interface ActionsDropdownProps {
  actions: ResourceConfig['extraActions']
  record: Record<string, unknown>
}

export function ActionsDropdown({ actions, record }: ActionsDropdownProps) {
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  useClickOutside(ref, () => setOpen(false), open)

  return (
    <div className="relative" ref={ref}>
      <Button
        variant="outline"
        size="icon-sm"
        onClick={() => setOpen(prev => !prev)}
        aria-label="More actions"
      >
        <MoreHorizontal className="size-4" />
      </Button>
      {open && (
        <div className="absolute right-0 top-full mt-1 z-10 min-w-36 rounded-md border border-border bg-surface shadow-md py-1">
          {actions.map(action => (
            <button
              key={action.label}
              type="button"
              className="w-full px-3 py-1.5 text-left text-sm text-fg hover:bg-surface-raised transition-colors"
              onClick={() => {
                action.action(record)
                setOpen(false)
              }}
            >
              {action.label}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
