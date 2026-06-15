/**
 * Tests that fully-custom pages (Dashboard, Settings) coexist with
 * dynamically generated resource links in the Sidebar (Step 16).
 *
 * The Sidebar has two hardcoded entries (Dashboard, Settings) that must
 * always render alongside whatever resources the registry provides.
 */
import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import type { ResourceConfig } from '@/types/resource'
import { Sidebar } from '@/components/layout/Sidebar'

// Shared flag controls admin state across tests without re-importing the module.
let mockIsAdmin = false

vi.mock('@/store/authStore', () => ({
  useAuthStore: (selector: (s: unknown) => unknown) =>
    selector({
      user: mockIsAdmin
        ? { id: 1, email: 'admin@test.com', role: 'admin', is_active: true }
        : null,
      token: mockIsAdmin ? 'test-token' : null,
      isAdmin: () => mockIsAdmin,
    }),
}))

afterEach(() => {
  mockIsAdmin = false
})

const generatedResources: ResourceConfig[] = [
  {
    key: 'plans',
    label: 'Plan',
    pluralLabel: 'Plans',
    endpoint: '/admin/plans',
    fields: [],
    relatedLists: [],
    extraActions: [],
  },
  {
    key: 'clients',
    label: 'Client',
    pluralLabel: 'Clients',
    endpoint: '/admin/clients',
    fields: [],
    relatedLists: [],
    extraActions: [],
  },
  {
    key: 'payments',
    label: 'Payment',
    pluralLabel: 'Payments',
    endpoint: '/admin/payments',
    fields: [],
    relatedLists: [],
    extraActions: [],
  },
]

function renderSidebar(resources: ResourceConfig[] = generatedResources) {
  return render(
    <MemoryRouter>
      <Sidebar resources={resources} />
    </MemoryRouter>,
  )
}

describe('Sidebar – custom page coexistence with generated resources', () => {
  it('renders hardcoded Dashboard link regardless of resource list', () => {
    renderSidebar()
    expect(screen.getByText('Dashboard')).toBeInTheDocument()
  })

  it('renders all generated resource links', () => {
    renderSidebar()
    expect(screen.getByText('Plans')).toBeInTheDocument()
    expect(screen.getByText('Clients')).toBeInTheDocument()
    expect(screen.getByText('Payments')).toBeInTheDocument()
  })

  it('Dashboard link still present alongside full 7-resource registry', () => {
    const fullRegistry: ResourceConfig[] = [
      'recipients', 'split-configs', 'plans', 'clients', 'payments', 'audit-logs', 'users',
    ].map(key => ({
      key,
      label: key,
      pluralLabel: key,
      endpoint: `/admin/${key}`,
      fields: [],
      relatedLists: [],
      extraActions: [],
    }))

    renderSidebar(fullRegistry)

    expect(screen.getByText('Dashboard')).toBeInTheDocument()
    // 7 resources + Dashboard = at least 8 nav links
    expect(screen.getAllByRole('link').length).toBeGreaterThanOrEqual(8)
  })

  it('renders correctly with empty resource list — only custom pages remain', () => {
    renderSidebar([])
    expect(screen.getByText('Dashboard')).toBeInTheDocument()
    expect(screen.queryByText('Plans')).not.toBeInTheDocument()
  })

  it('Settings link appears for admin user alongside generated resources', () => {
    mockIsAdmin = true
    renderSidebar()

    expect(screen.getByText('Dashboard')).toBeInTheDocument()
    expect(screen.getByText('Plans')).toBeInTheDocument()
    expect(screen.getByText('Settings')).toBeInTheDocument()
  })

  it('Settings link absent for non-admin users', () => {
    renderSidebar()

    expect(screen.queryByText('Settings')).not.toBeInTheDocument()
  })
})
