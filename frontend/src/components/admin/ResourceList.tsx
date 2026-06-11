import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useResource } from '@/hooks/useResource'
import { useDebounce } from '@/hooks/useDebounce'
import type { ResourceConfig } from '@/types/resource'
import { Spinner } from '@/components/ui'
import { ResourceListToolbar } from './ResourceListToolbar'
import { ResourceTable } from './ResourceTable'
import { ResourcePagination } from './ResourcePagination'
import type { SortOrder } from './ResourceTable'

export interface ResourceListProps {
  config: ResourceConfig
}

export function ResourceList({ config }: ResourceListProps) {
  const navigate = useNavigate()

  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const [search, setSearch] = useState('')
  const [sortBy, setSortBy] = useState<string | undefined>(undefined)
  const [sortOrder, setSortOrder] = useState<SortOrder>('asc')
  const [confirmDeleteId, setConfirmDeleteId] = useState<string | number | null>(null)

  const debouncedSearch = useDebounce(search, 300)

  const { list, remove } = useResource<Record<string, unknown>>(config.endpoint, {
    listParams: {
      page,
      pageSize,
      search: debouncedSearch || undefined,
      sortBy,
      sortOrder,
    },
  })

  const listFields = config.fields.filter(f => f.showInList)
  const hasFilterable = config.fields.some(f => f.filterable)
  // Resources without any showInForm fields are read-only (e.g. Payments, AuditLog)
  const isWritable = config.fields.some(f => f.showInForm)
  const hasActions = isWritable || config.extraActions.length > 0

  const total = list.data?.total ?? 0
  const totalPages = Math.max(1, Math.ceil(total / pageSize))
  const records = list.data?.data ?? []

  function handleSort(fieldKey: string) {
    if (sortBy === fieldKey) {
      setSortOrder(prev => (prev === 'asc' ? 'desc' : 'asc'))
    } else {
      setSortBy(fieldKey)
      setSortOrder('asc')
    }
    setPage(1)
  }

  function handleSearchChange(e: React.ChangeEvent<HTMLInputElement>) {
    setSearch(e.target.value)
    setPage(1)
  }

  function handlePageSizeChange(e: React.ChangeEvent<HTMLSelectElement>) {
    setPageSize(Number(e.target.value))
    setPage(1)
  }

  function handleDeleteConfirm(id: string | number) {
    remove.mutate(id, {
      onSuccess: () => setConfirmDeleteId(null),
    })
  }

  if (list.isLoading) {
    return (
      <div className="flex items-center justify-center py-16">
        <Spinner size="lg" />
      </div>
    )
  }

  if (list.isError) {
    return (
      <div className="rounded-md border border-danger/20 bg-danger/5 p-4 text-sm text-danger">
        Failed to load {config.pluralLabel.toLowerCase()}.{' '}
        {list.error?.message}
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <ResourceListToolbar
        config={config}
        search={search}
        hasFilterable={hasFilterable}
        isWritable={isWritable}
        onSearchChange={handleSearchChange}
      />
      <ResourceTable
        config={config}
        records={records}
        listFields={listFields}
        hasActions={hasActions}
        isWritable={isWritable}
        sortBy={sortBy}
        sortOrder={sortOrder}
        confirmDeleteId={confirmDeleteId}
        isDeleting={remove.isPending}
        onSort={handleSort}
        onEdit={id => navigate(`/${config.key}/${id}/edit`)}
        onDeleteRequest={setConfirmDeleteId}
        onDeleteConfirm={handleDeleteConfirm}
        onDeleteCancel={() => setConfirmDeleteId(null)}
      />
      <ResourcePagination
        page={page}
        pageSize={pageSize}
        total={total}
        totalPages={totalPages}
        onPageChange={setPage}
        onPageSizeChange={handlePageSizeChange}
      />
    </div>
  )
}
