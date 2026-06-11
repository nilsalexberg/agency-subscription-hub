import { ChevronLeft, ChevronRight } from 'lucide-react'
import { Button, Select } from '@/components/ui'

const PAGE_SIZE_OPTIONS = [10, 20, 50, 100] as const

interface ResourcePaginationProps {
  page: number
  pageSize: number
  total: number
  totalPages: number
  onPageChange: (page: number) => void
  onPageSizeChange: (e: React.ChangeEvent<HTMLSelectElement>) => void
}

export function ResourcePagination({
  page,
  pageSize,
  total,
  totalPages,
  onPageChange,
  onPageSizeChange,
}: ResourcePaginationProps) {
  const startRow = total === 0 ? 0 : (page - 1) * pageSize + 1
  const endRow = Math.min(page * pageSize, total)

  return (
    <div className="flex items-center justify-between text-sm text-fg-muted">
      <div className="flex items-center gap-2">
        <span>Rows per page:</span>
        <Select
          value={String(pageSize)}
          onChange={onPageSizeChange}
          className="w-[4.5rem] h-7 text-xs"
        >
          {PAGE_SIZE_OPTIONS.map(size => (
            <option key={size} value={size}>
              {size}
            </option>
          ))}
        </Select>
      </div>

      <div className="flex items-center gap-3">
        <span>
          {total === 0 ? '0' : `${startRow}–${endRow}`} of {total}
        </span>
        <div className="flex items-center gap-1">
          <Button
            variant="outline"
            size="icon-sm"
            disabled={page <= 1}
            aria-label="Previous page"
            onClick={() => onPageChange(page - 1)}
          >
            <ChevronLeft className="size-4" />
          </Button>
          <Button
            variant="outline"
            size="icon-sm"
            disabled={page >= totalPages}
            aria-label="Next page"
            onClick={() => onPageChange(page + 1)}
          >
            <ChevronRight className="size-4" />
          </Button>
        </div>
      </div>
    </div>
  )
}
