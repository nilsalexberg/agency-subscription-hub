import { createBrowserRouter, Navigate } from 'react-router-dom'
import { AppLayout } from '@/components/layout/AppLayout'
import { LoginPage } from '@/pages/auth/LoginPage'
import { RegisterPage } from '@/pages/auth/RegisterPage'
import { DashboardPage } from '@/pages/dashboard/DashboardPage'
import { SettingsPage } from '@/pages/settings/SettingsPage'
import { ResourceList } from '@/components/admin/ResourceList'
import { ResourceForm } from '@/components/admin/ResourceForm'
import { ResourceDetail } from '@/components/admin/ResourceDetail'
import { RESOURCES } from '@/resources'

const resourceRoutes = RESOURCES.flatMap((config) => {
  const writable = config.fields.some((f) => f.showInForm)

  const routes = [
    { path: `/${config.key}`, element: <ResourceList config={config} /> },
    { path: `/${config.key}/:id`, element: <ResourceDetail config={config} /> },
  ]

  if (writable) {
    routes.push(
      { path: `/${config.key}/new`, element: <ResourceForm config={config} mode="create" /> },
      { path: `/${config.key}/:id/edit`, element: <ResourceForm config={config} mode="edit" /> },
    )
  }

  return routes
})

export const router = createBrowserRouter([
  { path: '/login', element: <LoginPage /> },
  { path: '/register', element: <RegisterPage /> },
  {
    element: <AppLayout />,
    children: [
      { path: '/', element: <Navigate to="/dashboard" replace /> },
      { path: '/dashboard', element: <DashboardPage /> },
      { path: '/settings', element: <SettingsPage /> },
      ...resourceRoutes,
    ],
  },
])
