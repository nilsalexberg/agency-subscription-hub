import { NavLink } from 'react-router-dom'
import {
  BarChart3,
  BookOpen,
  CreditCard,
  History,
  Settings,
  Split,
  Users,
  UserSquare2,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { useAuthStore } from '@/store/authStore'

const navItems = [
  { to: '/dashboard', label: 'Dashboard', icon: BarChart3 },
  { to: '/plans', label: 'Plans', icon: BookOpen },
  { to: '/recipients', label: 'Recipients', icon: UserSquare2 },
  { to: '/split-configs', label: 'Split Configs', icon: Split },
  { to: '/clients', label: 'Clients', icon: Users },
  { to: '/payments', label: 'Payments', icon: CreditCard },
  { to: '/history', label: 'History', icon: History },
]

const adminItems = [
  { to: '/users', label: 'Users', icon: Users },
  { to: '/settings', label: 'Settings', icon: Settings },
]

export function Sidebar() {
  const isAdmin = useAuthStore((s) => s.isAdmin)

  return (
    <aside className="w-60 shrink-0 border-r bg-gray-50 flex flex-col h-screen sticky top-0">
      <div className="px-6 py-5 border-b">
        <span className="font-semibold text-gray-900">Subscription Hub</span>
      </div>
      <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-1">
        {navItems.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              cn(
                'flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors',
                isActive
                  ? 'bg-gray-900 text-white'
                  : 'text-gray-700 hover:bg-gray-200',
              )
            }
          >
            <Icon size={16} />
            {label}
          </NavLink>
        ))}
        {isAdmin() && (
          <>
            <div className="pt-4 pb-1 px-3">
              <span className="text-xs uppercase tracking-wider text-gray-400 font-medium">
                Admin
              </span>
            </div>
            {adminItems.map(({ to, label, icon: Icon }) => (
              <NavLink
                key={to}
                to={to}
                className={({ isActive }) =>
                  cn(
                    'flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors',
                    isActive
                      ? 'bg-gray-900 text-white'
                      : 'text-gray-700 hover:bg-gray-200',
                  )
                }
              >
                <Icon size={16} />
                {label}
              </NavLink>
            ))}
          </>
        )}
      </nav>
    </aside>
  )
}
