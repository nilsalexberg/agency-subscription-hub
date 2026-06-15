import { NavLink } from 'react-router-dom'
import { BarChart3, Settings } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useAuthStore } from '@/store/authStore'
import type { ResourceConfig } from '@/types/resource'

interface SidebarProps {
  resources: ResourceConfig[]
}

const linkClass = ({ isActive }: { isActive: boolean }) =>
  cn(
    'flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors',
    isActive ? 'bg-gray-900 text-white' : 'text-gray-700 hover:bg-gray-200',
  )

export function Sidebar({ resources }: SidebarProps) {
  const isAdmin = useAuthStore((s) => s.isAdmin)

  return (
    <aside className="w-60 shrink-0 border-r bg-gray-50 flex flex-col h-screen sticky top-0">
      <div className="px-6 py-5 border-b">
        <span className="font-semibold text-gray-900">Subscription Hub</span>
      </div>
      <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-1">
        <NavLink to="/dashboard" className={linkClass}>
          <BarChart3 size={16} />
          Dashboard
        </NavLink>

        {resources.map((resource) => (
          <NavLink
            key={resource.key}
            to={`/${resource.key}`}
            end={false}
            className={linkClass}
          >
            {resource.pluralLabel}
          </NavLink>
        ))}

        {isAdmin() && (
          <>
            <div className="pt-4 pb-1 px-3">
              <span className="text-xs uppercase tracking-wider text-gray-400 font-medium">
                Admin
              </span>
            </div>
            <NavLink to="/settings" className={linkClass}>
              <Settings size={16} />
              Settings
            </NavLink>
          </>
        )}
      </nav>
    </aside>
  )
}
