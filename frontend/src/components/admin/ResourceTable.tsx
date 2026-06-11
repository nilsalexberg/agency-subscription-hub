import { ChevronDown, ChevronUp, ChevronsUpDown, Check, X } from 'lucide-react'
import type { ResourceConfig, FieldDescriptor } from '@/types/resource'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui'
import { RowActions } from './RowActions'

export type SortOrder = 'asc' | 'desc'

function SortIndicator({
  field,
  sortBy,
  sortOrder,
}: {
  field: string
  sortBy: string | undefined
  sortOrder: SortOrder
}) {
  if (sortBy !== field) {
    return <ChevronsUpDown className="inline size-3.5 ml-1 opacity-40" />
  }
  return sortOrder === 'asc' ? (
    <ChevronUp className="inline size-3.5 ml-1 text-primary" />
  ) : (
    <ChevronDown className="inline size-3.5 ml-1 text-primary" />
  )
}

export function resolveCellValue(field: FieldDescriptor, record: Record<string, unknown>): React.ReactNode {
  if (field.renderCell) {
    return field.renderCell(record)
  }

  if (field.type === 'relation' && field.relation) {
    // Backend serializes relation display values as `{attribute}_{labelField}`.
    // Derive attribute name by stripping the `_id` FK suffix.
    const attribute = field.key.replace(/_id$/, '')
    const resolvedKey = `${attribute}_${field.relation.labelField}`
    const resolved = record[resolvedKey]
    if (resolved !== undefined) return String(resolved)
  }

  const value = record[field.key]

  if (value === null || value === undefined) {
    return <span className="text-fg-muted">—</span>
  }
  if (typeof value === 'boolean') {
    return value ? (
      <Check className="text-success size-4" />
    ) : (
      <X className="text-danger size-4" />
    )
  }

  return String(value)
}


export interface ResourceTableProps {
  config: ResourceConfig
  records: Record<string, unknown>[]
  listFields: FieldDescriptor[]
  hasActions: boolean
  isWritable: boolean
  sortBy: string | undefined
  sortOrder: SortOrder
  confirmDeleteId: string | number | null
  isDeleting: boolean
  onSort: (fieldKey: string) => void
  onEdit: (id: string | number) => void
  onDeleteRequest: (id: string | number) => void
  onDeleteConfirm: (id: string | number) => void
  onDeleteCancel: () => void
}

export function ResourceTable({
  config,
  records,
  listFields,
  hasActions,
  isWritable,
  sortBy,
  sortOrder,
  confirmDeleteId,
  isDeleting,
  onSort,
  onEdit,
  onDeleteRequest,
  onDeleteConfirm,
  onDeleteCancel,
}: ResourceTableProps) {
  return (
    <div className="rounded-lg border border-border overflow-hidden">
      <Table>
        <TableHeader>
          <TableRow>
            {listFields.map(field => (
              <TableHead key={field.key}>
                {field.sortable ? (
                  <button
                    type="button"
                    onClick={() => onSort(field.key)}
                    className="flex items-center gap-0.5 hover:text-fg transition-colors"
                  >
                    {field.label}
                    <SortIndicator field={field.key} sortBy={sortBy} sortOrder={sortOrder} />
                  </button>
                ) : (
                  field.label
                )}
              </TableHead>
            ))}
            {hasActions && <TableHead className="text-right w-px whitespace-nowrap">Actions</TableHead>}
          </TableRow>
        </TableHeader>
        <TableBody>
          {records.length === 0 ? (
            <TableRow>
              <TableCell
                colSpan={listFields.length + (hasActions ? 1 : 0)}
                className="py-12 text-center text-fg-muted"
              >
                No {config.pluralLabel.toLowerCase()} found.
              </TableCell>
            </TableRow>
          ) : (
            records.map(record => {
              const id = record['id'] as string | number
              const isConfirmingDelete = confirmDeleteId === id
              const isDeletingThis = isDeleting && confirmDeleteId === id

              return (
                <TableRow key={id}>
                  {listFields.map(field => (
                    <TableCell key={field.key}>
                      {resolveCellValue(field, record)}
                    </TableCell>
                  ))}

                  {hasActions && (
                    <TableCell className="text-right">
                      <RowActions
                        record={record}
                        id={id}
                        config={config}
                        isWritable={isWritable}
                        isConfirmingDelete={isConfirmingDelete}
                        isDeletingThis={isDeletingThis}
                        onEdit={onEdit}
                        onDeleteRequest={onDeleteRequest}
                        onDeleteConfirm={onDeleteConfirm}
                        onDeleteCancel={onDeleteCancel}
                      />
                    </TableCell>
                  )}
                </TableRow>
              )
            })
          )}
        </TableBody>
      </Table>
    </div>
  )
}
