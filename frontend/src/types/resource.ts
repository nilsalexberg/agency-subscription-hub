import type React from 'react'

export interface FieldDescriptor {
  key: string
  label: string
  type: 'text' | 'email' | 'number' | 'boolean' | 'select' | 'date' | 'textarea' | 'relation'
  showInList: boolean
  showInForm: boolean
  showInDetail: boolean
  required: boolean
  sortable: boolean
  filterable: boolean
  readonly: boolean
  selectOptions?: { label: string; value: string | number }[]
  relation?: {
    resource: string
    labelField: string
    valueField: string
  }
  renderCell?: (record: unknown) => React.ReactNode
  renderInput?: (field: FieldDescriptor, form: unknown) => React.ReactNode
}

export interface ResourceConfig {
  key: string
  label: string
  pluralLabel: string
  endpoint: string
  fields: FieldDescriptor[]
  relatedLists: {
    label: string
    resource: string
    foreignKey: string
    fields: FieldDescriptor[]
  }[]
  extraActions: {
    label: string
    variant: string
    action: (record: unknown) => void
  }[]
}
