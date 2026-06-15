/**
 * Unit tests for the resolveCellValue escape hatch (Step 16).
 *
 * resolveCellValue is the single point where list and detail cells are
 * rendered. The `renderCell` field option is the primary escape hatch:
 * it fully replaces all resolution logic for that field.
 */
import { describe, it, expect, vi } from 'vitest'
import type { FieldDescriptor } from '@/types/resource'
import { resolveCellValue } from '@/components/admin/ResourceTable'

const baseField: FieldDescriptor = {
  key: 'name',
  label: 'Name',
  type: 'text',
  showInList: true,
  showInForm: true,
  showInDetail: true,
  required: true,
  sortable: true,
  filterable: true,
  readonly: false,
}

const relationField: FieldDescriptor = {
  key: 'plan_id',
  label: 'Plan',
  type: 'relation',
  showInList: true,
  showInForm: true,
  showInDetail: true,
  required: false,
  sortable: false,
  filterable: false,
  readonly: false,
  relation: { resource: 'plans', labelField: 'name', valueField: 'id' },
}

describe('resolveCellValue – renderCell escape hatch', () => {
  it('calls renderCell with the full record and returns its result', () => {
    const renderCell = vi.fn().mockReturnValue('CUSTOM_OUTPUT')
    const field: FieldDescriptor = { ...baseField, renderCell }

    const record = { name: 'Acme', status: 'active' }
    const result = resolveCellValue(field, record)

    expect(renderCell).toHaveBeenCalledOnce()
    expect(renderCell).toHaveBeenCalledWith(record)
    expect(result).toBe('CUSTOM_OUTPUT')
  })

  it('renderCell takes priority over relation display key resolution', () => {
    const renderCell = vi.fn().mockReturnValue('OVERRIDE')
    const field: FieldDescriptor = { ...relationField, renderCell }

    const record = { plan_id: 1, plan_name: 'Starter' }
    const result = resolveCellValue(field, record)

    expect(result).toBe('OVERRIDE')
    expect(renderCell).toHaveBeenCalledWith(record)
  })

  it('renderCell takes priority over boolean icon rendering', () => {
    const renderCell = vi.fn().mockReturnValue('YES')
    const field: FieldDescriptor = {
      ...baseField,
      key: 'is_active',
      type: 'boolean',
      renderCell,
    }

    const result = resolveCellValue(field, { is_active: true })
    expect(result).toBe('YES')
  })
})

describe('resolveCellValue – relation display key resolution', () => {
  it('resolves {attribute}_{labelField} key from backend-serialized data', () => {
    // Backend serializes Plan relation as `plan_name` (strips _id suffix, appends _name)
    const result = resolveCellValue(relationField, { plan_id: 5, plan_name: 'Enterprise' })
    expect(result).toBe('Enterprise')
  })

  it('returns raw FK value when display key is absent', () => {
    // No plan_name in record — falls back to plan_id value
    const result = resolveCellValue(relationField, { plan_id: 5 })
    expect(result).toBe('5')
  })
})

describe('resolveCellValue – standard value resolution', () => {
  it('returns string value for text fields', () => {
    const result = resolveCellValue(baseField, { name: 'Widget Co' })
    expect(result).toBe('Widget Co')
  })

  it('returns null node for missing field value', () => {
    const result = resolveCellValue(baseField, {})
    // Null/undefined renders a React element (dash), not a string
    expect(typeof result).toBe('object')
    expect(result).not.toBeNull()
  })
})
