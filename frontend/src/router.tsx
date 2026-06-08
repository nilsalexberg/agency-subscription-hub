import { createBrowserRouter, Navigate } from 'react-router-dom'
import { AppLayout } from '@/components/layout/AppLayout'
import { LoginPage } from '@/pages/auth/LoginPage'
import { DashboardPage } from '@/pages/dashboard/DashboardPage'
import { PlansPage } from '@/pages/plans/PlansPage'
import { PlanFormPage } from '@/pages/plans/PlanFormPage'
import { RecipientsPage } from '@/pages/recipients/RecipientsPage'
import { RecipientFormPage } from '@/pages/recipients/RecipientFormPage'
import { SplitConfigsPage } from '@/pages/split-configs/SplitConfigsPage'
import { SplitConfigFormPage } from '@/pages/split-configs/SplitConfigFormPage'
import { ClientsPage } from '@/pages/clients/ClientsPage'
import { ClientFormPage } from '@/pages/clients/ClientFormPage'
import { PaymentsPage } from '@/pages/payments/PaymentsPage'
import { HistoryPage } from '@/pages/history/HistoryPage'
import { UsersPage } from '@/pages/users/UsersPage'
import { UserFormPage } from '@/pages/users/UserFormPage'
import { SettingsPage } from '@/pages/settings/SettingsPage'

export const router = createBrowserRouter([
  { path: '/login', element: <LoginPage /> },
  {
    element: <AppLayout />,
    children: [
      { path: '/', element: <Navigate to="/dashboard" replace /> },
      { path: '/dashboard', element: <DashboardPage /> },
      { path: '/plans', element: <PlansPage /> },
      { path: '/plans/new', element: <PlanFormPage /> },
      { path: '/plans/:id/edit', element: <PlanFormPage /> },
      { path: '/recipients', element: <RecipientsPage /> },
      { path: '/recipients/new', element: <RecipientFormPage /> },
      { path: '/recipients/:id/edit', element: <RecipientFormPage /> },
      { path: '/split-configs', element: <SplitConfigsPage /> },
      { path: '/split-configs/new', element: <SplitConfigFormPage /> },
      { path: '/split-configs/:id/edit', element: <SplitConfigFormPage /> },
      { path: '/clients', element: <ClientsPage /> },
      { path: '/clients/new', element: <ClientFormPage /> },
      { path: '/clients/:id/edit', element: <ClientFormPage /> },
      { path: '/payments', element: <PaymentsPage /> },
      { path: '/history', element: <HistoryPage /> },
      { path: '/users', element: <UsersPage /> },
      { path: '/users/new', element: <UserFormPage /> },
      { path: '/users/:id/edit', element: <UserFormPage /> },
      { path: '/settings', element: <SettingsPage /> },
    ],
  },
])
