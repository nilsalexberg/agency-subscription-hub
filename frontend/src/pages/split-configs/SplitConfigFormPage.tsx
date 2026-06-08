import { useParams } from 'react-router-dom'

export function SplitConfigFormPage() {
  const { id } = useParams()
  const isEdit = Boolean(id)

  return (
    <div>
      <h1 className="text-2xl font-semibold text-gray-900 mb-6">
        {isEdit ? 'Edit Split Config' : 'New Split Config'}
      </h1>
      <div className="border rounded-lg bg-white p-4 max-w-lg">
        <p className="text-sm text-gray-400">Form not implemented yet.</p>
      </div>
    </div>
  )
}
