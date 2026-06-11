import { Controller } from 'react-hook-form'
import type { UseFormReturn } from 'react-hook-form'
import type { FieldDescriptor } from '@/types/resource'
import { Checkbox, Input, Select, Textarea } from '@/components/ui'
import { RelationSelect } from './RelationSelect'

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type AnyFormValues = Record<string, any>
type FormMethods = UseFormReturn<AnyFormValues>

interface ResourceFormInputProps {
  field: FieldDescriptor
  methods: FormMethods
}

export function ResourceFormInput({ field, methods }: ResourceFormInputProps) {
  const { register, control, formState: { errors } } = methods
  const hasError = Boolean(errors[field.key])

  switch (field.type) {
    case 'boolean':
      return (
        <Controller
          name={field.key}
          control={control}
          render={({ field: f }) => (
            <Checkbox
              id={field.key}
              checked={Boolean(f.value)}
              onChange={e => f.onChange(e.target.checked)}
            />
          )}
        />
      )

    case 'textarea':
      return (
        <Textarea
          id={field.key}
          error={hasError}
          {...register(field.key)}
        />
      )

    case 'select':
      return (
        <Select
          id={field.key}
          error={hasError}
          {...register(field.key)}
        >
          <option value="">Select…</option>
          {field.selectOptions?.map(opt => (
            <option key={String(opt.value)} value={String(opt.value)}>
              {opt.label}
            </option>
          ))}
        </Select>
      )

    case 'relation':
      return (
        <Controller
          name={field.key}
          control={control}
          render={({ field: f }) => (
            <RelationSelect
              id={field.key}
              field={field}
              value={f.value as string | number}
              onChange={f.onChange}
              error={hasError}
            />
          )}
        />
      )

    case 'number':
      return (
        <Input
          id={field.key}
          type="number"
          error={hasError}
          {...register(field.key)}
        />
      )

    default:
      return (
        <Input
          id={field.key}
          type={field.type === 'email' ? 'email' : field.type === 'date' ? 'date' : 'text'}
          error={hasError}
          {...register(field.key)}
        />
      )
  }
}
