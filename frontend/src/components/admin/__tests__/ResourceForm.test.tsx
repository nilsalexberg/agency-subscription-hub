/**
 * Tests for the ResourceForm renderInput escape hatch (Step 16).
 *
 * renderInput is the per-field escape hatch that replaces the standard
 * input component entirely. It receives the FieldDescriptor and react-hook-form
 * methods so custom inputs can register themselves with the form.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import type { FieldDescriptor, ResourceConfig } from '@/types/resource'
import { ResourceForm } from '@/components/admin/ResourceForm'

vi.mock('@/hooks/useResource', () => ({
  useResource: () => ({
    detail: { isLoading: false, isError: false, data: null },
    create: { mutateAsync: vi.fn(), error: null, isPending: false },
    update: { mutateAsync: vi.fn(), error: null, isPending: false },
    list: { isLoading: false, isError: false, data: null },
    remove: { mutate: vi.fn(), isPending: false },
  }),
}))

const nameField: FieldDescriptor = {
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

const minimalConfig: ResourceConfig = {
  key: 'widgets',
  label: 'Widget',
  pluralLabel: 'Widgets',
  endpoint: '/admin/widgets',
  fields: [nameField],
  relatedLists: [],
  extraActions: [],
}

function renderForm(config: ResourceConfig, mode: 'create' | 'edit' = 'create') {
  return render(
    <MemoryRouter>
      <ResourceForm config={config} mode={mode} />
    </MemoryRouter>,
  )
}

describe('ResourceForm – renderInput escape hatch', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders custom input element when renderInput is provided', () => {
    const config: ResourceConfig = {
      ...minimalConfig,
      fields: [
        {
          ...nameField,
          renderInput: () => <input data-testid="custom-name-input" />,
        },
      ],
    }

    renderForm(config)

    expect(screen.getByTestId('custom-name-input')).toBeInTheDocument()
  })

  it('does not render the standard input when renderInput replaces it', () => {
    const config: ResourceConfig = {
      ...minimalConfig,
      fields: [
        {
          ...nameField,
          renderInput: () => <input data-testid="custom-name-input" />,
        },
      ],
    }

    renderForm(config)

    // The default ResourceFormInput renders <input id="name">
    // With renderInput override, that element should not exist.
    expect(document.querySelector('input#name')).toBeNull()
    expect(screen.getByTestId('custom-name-input')).toBeInTheDocument()
  })

  it('calls renderInput with field descriptor and form methods', () => {
    const renderInput = vi.fn(
      (_field: FieldDescriptor, _form: unknown) => (
        <input data-testid="spy-input" />
      ),
    )
    const config: ResourceConfig = {
      ...minimalConfig,
      fields: [{ ...nameField, renderInput }],
    }

    renderForm(config)

    expect(renderInput).toHaveBeenCalled()
    // Verify the arguments passed to any call (component may render more than once)
    const [receivedField, receivedMethods] = renderInput.mock.calls[0] as [FieldDescriptor, Record<string, unknown>]
    expect(receivedField.key).toBe('name')
    expect(typeof receivedMethods['register']).toBe('function')
    expect(typeof receivedMethods['control']).toBe('object')
  })

  it('renders standard input when renderInput is not set', () => {
    renderForm(minimalConfig)

    // Default input has id matching the field key
    expect(document.querySelector('input#name')).toBeInTheDocument()
    expect(screen.queryByTestId('custom-name-input')).not.toBeInTheDocument()
  })

  it('multiple fields can each have independent renderInput overrides', () => {
    const descriptionField: FieldDescriptor = {
      key: 'description',
      label: 'Description',
      type: 'textarea',
      showInList: false,
      showInForm: true,
      showInDetail: true,
      required: false,
      sortable: false,
      filterable: false,
      readonly: false,
    }

    const config: ResourceConfig = {
      ...minimalConfig,
      fields: [
        {
          ...nameField,
          renderInput: () => <input data-testid="custom-name" />,
        },
        {
          ...descriptionField,
          renderInput: () => <textarea data-testid="custom-description" />,
        },
      ],
    }

    renderForm(config)

    expect(screen.getByTestId('custom-name')).toBeInTheDocument()
    expect(screen.getByTestId('custom-description')).toBeInTheDocument()
  })
})
