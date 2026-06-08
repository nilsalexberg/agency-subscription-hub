import { Link } from 'react-router-dom'

export function PlansPage() {
  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-semibold text-gray-900">Plans</h1>
        <Link
          to="/plans/new"
          className="px-4 py-2 bg-gray-900 text-white text-sm rounded-md hover:bg-gray-700"
        >
          New Plan
        </Link>
      </div>
      <div className="border rounded-lg bg-white">
        <p className="text-sm text-gray-400 p-4">Not implemented yet.</p>
      </div>
    </div>
  )
}
