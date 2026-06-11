import { Pencil, Trash2 } from 'lucide-react'
import type { ResourceConfig } from '@/types/resource'
import { Button, Spinner } from '@/components/ui'
import { ActionsDropdown } from './ActionsDropdown'

type ButtonVariant = 'primary' | 'secondary' | 'outline' | 'ghost' | 'destructive' | 'link'

export interface RowActionsProps {
  record: Record<string, unknown>
  id: string | number
  config: Pick<ResourceConfig, 'extraActions'>
  isWritable: boolean
  isConfirmingDelete: boolean
  isDeletingThis: boolean
  onEdit: (id: string | number) => void
  onDeleteRequest: (id: string | number) => void
  onDeleteConfirm: (id: string | number) => void
  onDeleteCancel: () => void
}

export function RowActions({
  record,
  id,
  config,
  isWritable,
  isConfirmingDelete,
  isDeletingThis,
  onEdit,
  onDeleteRequest,
  onDeleteConfirm,
  onDeleteCancel,
}: RowActionsProps) {
  return (
    <div className="flex items-center justify-end gap-1.5">
      {config.extraActions.length > 0 && config.extraActions.length <= 2 &&
        config.extraActions.map(action => (
          <Button
            key={action.label}
            variant={action.variant as ButtonVariant}
            size="sm"
            onClick={() => action.action(record)}
          >
            {action.label}
          </Button>
        ))
      }

      {config.extraActions.length > 2 && (
        <ActionsDropdown actions={config.extraActions} record={record} />
      )}

      {isWritable && !isConfirmingDelete && (
        <>
          <Button variant="ghost" size="icon-sm" aria-label="Edit" onClick={() => onEdit(id)}>
            <Pencil className="size-3.5" />
          </Button>
          <Button variant="ghost" size="icon-sm" aria-label="Delete" onClick={() => onDeleteRequest(id)}>
            <Trash2 className="size-3.5 text-danger" />
          </Button>
        </>
      )}

      {isWritable && isConfirmingDelete && (
        <>
          <span className="text-xs text-fg-muted">Delete?</span>
          <Button
            variant="destructive"
            size="sm"
            disabled={isDeletingThis}
            onClick={() => onDeleteConfirm(id)}
          >
            {isDeletingThis ? <Spinner size="sm" /> : 'Yes'}
          </Button>
          <Button variant="ghost" size="sm" onClick={onDeleteCancel}>
            No
          </Button>
        </>
      )}
    </div>
  )
}
