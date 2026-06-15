import { LogOut } from 'lucide-react'
import { useAuthStore } from '@/store/authStore'

export function Header() {
  const { user, logout } = useAuthStore()

  return (
    <header className="h-14 border-b flex items-center justify-between px-6 bg-white">
      <span className="text-sm font-semibold text-gray-900">Admin Panel</span>
      <div className="flex items-center gap-4">
        <span className="text-sm text-gray-600">{user?.email}</span>
        <button
          onClick={logout}
          className="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-900 transition-colors"
        >
          <LogOut size={14} />
          Logout
        </button>
      </div>
    </header>
  )
}
