import type { FieldDescriptor } from '@/types/resource'
import { useResource } from '@/hooks/useResource'
import {
  Spinner,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui'
import { resolveCellValue } from './ResourceTable'

interface RelatedListProps {
  label: string
  resource: string
  foreignKey: string
  fields: FieldDescriptor[]
  parentId: string | number
}

export function RelatedList({
  label,
  resource,
  foreignKey,
  fields,
  parentId,
}: RelatedListProps) {
  const { list } = useResource<Record<string, unknown>>(resource, {
    listParams: { pageSize: 50, filters: { [foreignKey]: parentId } },
  })

  const visibleFields = fields.filter(f => f.showInList)

  return (
    <section className="space-y-2">
      <h3 className="text-sm font-semibold text-fg-muted uppercase tracking-wider">{label}</h3>
      <div className="rounded-lg border border-border overflow-hidden">
        {list.isLoading ? (
          <div className="flex justify-center py-8">
            <Spinner size="sm" />
          </div>
        ) : list.isError ? (
          <p className="py-4 px-4 text-sm text-danger">Failed to load {label.toLowerCase()}.</p>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                {visibleFields.map(f => (
                  <TableHead key={f.key}>{f.label}</TableHead>
                ))}
              </TableRow>
            </TableHeader>
            <TableBody>
              {(list.data?.data ?? []).length === 0 ? (
                <TableRow>
                  <TableCell colSpan={visibleFields.length} className="py-8 text-center text-fg-muted">
                    No {label.toLowerCase()} found.
                  </TableCell>
                </TableRow>
              ) : (
                (list.data?.data ?? []).map((record, i) => (
                  <TableRow key={(record['id'] as string | number | undefined) ?? i}>
                    {visibleFields.map(f => (
                      <TableCell key={f.key}>{resolveCellValue(f, record)}</TableCell>
                    ))}
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        )}
      </div>
    </section>
  )
}
