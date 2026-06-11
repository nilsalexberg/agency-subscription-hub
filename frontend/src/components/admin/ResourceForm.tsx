import { useEffect, useMemo } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import type { FieldDescriptor, ResourceConfig } from '@/types/resource'
import { useResource } from '@/hooks/useResource'
import {
  Alert,
  Button,
  FormField,
  Spinner,
} from '@/components/ui'
import { resolveCellValue } from './ResourceTable'
import { ResourceFormInput } from './ResourceFormInput'

export interface ResourceFormProps {
  config: ResourceConfig
  mode: 'create' | 'edit'
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type AnyFormValues = Record<string, any>

function buildZodSchema(fields: FieldDescriptor[]) {
  const shape: Record<string, z.ZodTypeAny> = {}
  for (const field of fields) {
    if (!field.showInForm || field.readonly) continue
    switch (field.type) {
      case 'boolean':
        shape[field.key] = z.boolean()
        break
      case 'number':
        shape[field.key] = z.coerce.number()
        break
      default:
        shape[field.key] = field.required
          ? z.string().min(1, 'Required')
          : z.string()
    }
  }
  return z.object(shape)
}

function buildDefaultValues(fields: FieldDescriptor[]): AnyFormValues {
  return Object.fromEntries(
    fields
      .filter(f => f.showInForm && !f.readonly)
      .map(f => [f.key, f.type === 'boolean' ? false : ''])
  )
}

export function ResourceForm({ config, mode }: ResourceFormProps) {
  const navigate = useNavigate()
  const { id } = useParams<{ id: string }>()
  const recordId = id ? (Number.isNaN(Number(id)) ? id : Number(id)) : undefined

  const formFields = useMemo(
    () => config.fields.filter(f => f.showInForm),
    [config.fields],
  )

  const schema = useMemo(() => buildZodSchema(config.fields), [config.fields])

  const methods = useForm<AnyFormValues>({
    resolver: zodResolver(schema),
    defaultValues: buildDefaultValues(formFields),
  })
  const { handleSubmit, reset, formState: { errors, isSubmitting } } = methods

  const { detail, create, update } = useResource<Record<string, unknown>>(config.endpoint, {
    id: mode === 'edit' ? recordId : undefined,
  })

  useEffect(() => {
    if (mode !== 'edit' || !detail.data) return
    const patch: AnyFormValues = {}
    for (const field of formFields) {
      if (field.readonly) continue
      const val = detail.data[field.key]
      patch[field.key] = val !== null && val !== undefined
        ? val
        : field.type === 'boolean' ? false : ''
    }
    reset(patch)
  }, [detail.data, mode, formFields, reset])

  async function onSubmit(values: AnyFormValues) {
    try {
      if (mode === 'create') {
        await create.mutateAsync(values)
      } else {
        await update.mutateAsync({ id: recordId!, payload: values })
      }
      navigate(`/${config.key}`)
    } catch {
      // Error displayed via mutation error state below
    }
  }

  if (mode === 'edit' && detail.isLoading) {
    return (
      <div className="flex items-center justify-center py-16">
        <Spinner size="lg" />
      </div>
    )
  }

  if (mode === 'edit' && detail.isError) {
    return (
      <Alert variant="danger">
        Failed to load record. {detail.error?.message}
      </Alert>
    )
  }

  const mutationError = create.error ?? update.error

  return (
    <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-5 max-w-lg">
      {mutationError && (
        <Alert variant="danger">{mutationError.message}</Alert>
      )}

      {formFields.map(field => {
        const errorMsg = (errors[field.key] as { message?: string } | undefined)?.message

        if (field.readonly) {
          return (
            <FormField key={field.key} label={field.label}>
              <div className="py-2 text-sm text-fg flex items-center min-h-[38px]">
                {resolveCellValue(field, (detail.data ?? {}) as Record<string, unknown>)}
              </div>
            </FormField>
          )
        }

        const input = field.renderInput
          ? field.renderInput(field, methods)
          : <ResourceFormInput field={field} methods={methods} />

        return (
          <FormField
            key={field.key}
            label={field.label}
            required={field.required}
            error={errorMsg}
            htmlFor={field.key}
          >
            {input}
          </FormField>
        )
      })}

      <div className="flex gap-3 pt-2">
        <Button type="submit" disabled={isSubmitting}>
          {isSubmitting
            ? 'Saving…'
            : mode === 'create'
              ? `Create ${config.label}`
              : 'Save Changes'}
        </Button>
        <Button
          type="button"
          variant="secondary"
          onClick={() => navigate(`/${config.key}`)}
        >
          Cancel
        </Button>
      </div>
    </form>
  )
}

