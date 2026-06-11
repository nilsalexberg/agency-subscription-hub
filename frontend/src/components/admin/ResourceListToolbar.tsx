import { useNavigate } from 'react-router-dom'
import type { ResourceConfig } from '@/types/resource'
import { Button, Input } from '@/components/ui'

interface ResourceListToolbarProps {
  config: ResourceConfig
  search: string
  hasFilterable: boolean
  isWritable: boolean
  onSearchChange: (e: React.ChangeEvent<HTMLInputElement>) => void
}

export function ResourceListToolbar({
  config,
  search,
  hasFilterable,
  isWritable,
  onSearchChange,
}: ResourceListToolbarProps) {
  const navigate = useNavigate()

  return (
    <div className="flex items-center justify-between gap-4">
      {hasFilterable ? (
        <Input
          type="search"
          placeholder={`Search ${config.pluralLabel.toLowerCase()}…`}
          value={search}
          onChange={onSearchChange}
          className="max-w-xs"
        />
      ) : (
        <div />
      )}
      {isWritable && (
        <Button size="sm" onClick={() => navigate(`/${config.key}/new`)}>
          New {config.label}
        </Button>
      )}
    </div>
  )
}
