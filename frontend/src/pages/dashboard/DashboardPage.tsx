export function DashboardPage() {
  return (
    <div>
      <h1 className="text-2xl font-semibold text-gray-900 mb-6">Dashboard</h1>
      <div className="grid grid-cols-4 gap-4 mb-8">
        {['Active Clients', 'Overdue', 'Cancelled', 'Monthly Revenue'].map((label) => (
          <div key={label} className="border rounded-lg p-4 bg-white">
            <p className="text-sm text-gray-500">{label}</p>
            <p className="text-2xl font-semibold text-gray-900 mt-1">—</p>
          </div>
        ))}
      </div>
      <div className="border rounded-lg p-4 bg-white">
        <h2 className="text-base font-medium text-gray-900 mb-3">Recent Payments</h2>
        <p className="text-sm text-gray-400">Not implemented yet.</p>
      </div>
    </div>
  )
}
