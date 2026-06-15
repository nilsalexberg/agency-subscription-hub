import { useNavigate, useParams } from 'react-router-dom'
import type { ResourceConfig } from '@/types/resource'
import { useResource } from '@/hooks/useResource'
import { Alert, Button, Spinner } from '@/components/ui'
import { resolveCellValue } from './ResourceTable'
import { RelatedList } from './RelatedList'

export interface ResourceDetailProps {
  config: ResourceConfig
}

export function ResourceDetail({ config }: ResourceDetailProps) {
  const navigate = useNavigate()
  const { id } = useParams<{ id: string }>()
  const recordId = id ? (Number.isNaN(Number(id)) ? id : Number(id)) : undefined

  const { detail } = useResource<Record<string, unknown>>(config.endpoint, {
    id: recordId,
  })

  const isWritable = config.fields.some(f => f.showInForm)
  const detailFields = config.fields.filter(f => f.showInDetail)

  if (detail.isLoading) {
    return (
      <div className="flex items-center justify-center py-16">
        <Spinner size="lg" />
      </div>
    )
  }

  if (detail.isError) {
    return <Alert variant="danger">Failed to load record. {detail.error?.message}</Alert>
  }

  const record = detail.data ?? {}

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between gap-4">
        <Button variant="secondary" size="sm" onClick={() => navigate(`/${config.key}`)}>
          ← Back
        </Button>
        {isWritable && (
          <Button size="sm" onClick={() => navigate(`/${config.key}/${recordId}/edit`)}>
            Edit
          </Button>
        )}
      </div>

      <section className="rounded-lg border border-border overflow-hidden">
        <dl className="divide-y divide-border">
          {detailFields.map(field => (
            <div key={field.key} className="grid grid-cols-3 gap-4 px-5 py-3">
              <dt className="text-sm font-medium text-fg-muted">{field.label}</dt>
              <dd className="col-span-2 text-sm text-fg">{resolveCellValue(field, record)}</dd>
            </div>
          ))}
          {detailFields.length === 0 && (
            <div className="px-5 py-8 text-center text-sm text-fg-muted">No details configured.</div>
          )}
        </dl>
      </section>

      {config.relatedLists.map(rel => (
        <RelatedList
          key={rel.resource}
          label={rel.label}
          resource={rel.resource}
          foreignKey={rel.foreignKey}
          fields={rel.fields}
          parentId={recordId!}
        />
      ))}
    </div>
  )
}
