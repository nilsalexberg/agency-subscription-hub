import { create } from 'zustand'
import { persist } from 'zustand/middleware'

type Role = 'admin' | 'viewer'

interface User {
  id: number
  email: string
  role: Role
  is_active: boolean
}

interface AuthState {
  user: User | null
  token: string | null
  login: (user: User, token: string) => void
  logout: () => void
  isAdmin: () => boolean
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      login: (user, token) => set({ user, token }),
      logout: () => set({ user: null, token: null }),
      isAdmin: () => get().user?.role === 'admin',
    }),
    { name: 'auth' },
  ),
)
