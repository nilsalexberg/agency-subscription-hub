import { useResource } from '@/hooks/useResource'
import { Select } from '@/components/ui'
import type { FieldDescriptor } from '@/types/resource'

interface RelationSelectProps {
  id?: string
  field: FieldDescriptor
  value: string | number
  onChange: (value: string | number) => void
  error?: boolean
  disabled?: boolean
}

export function RelationSelect({ id, field, value, onChange, error, disabled }: RelationSelectProps) {
  const { labelField, valueField } = field.relation!

  const { list } = useResource<Record<string, unknown>>(field.relation!.resource, {
    listParams: { page: 1, pageSize: 100 },
  })

  return (
    <Select
      id={id}
      value={String(value ?? '')}
      onChange={e => onChange(e.target.value)}
      error={error}
      disabled={disabled || list.isLoading}
    >
      <option value="">
        {list.isLoading ? 'Loading…' : `Select ${field.label}…`}
      </option>
      {list.data?.data.map(record => (
        <option
          key={String(record[valueField])}
          value={String(record[valueField])}
        >
          {String(record[labelField])}
        </option>
      ))}
    </Select>
  )
}
