const mockRouter = { push: jest.fn(), back: jest.fn(), replace: jest.fn() }
jest.mock('@/components/ui/TerminalHeader', function() { return { TerminalHeader: function() { return null } } })
jest.mock('@/components/ui/SurfaceCard', function() { return { SurfaceCard: function({ children }) { return children } } })
jest.mock('@/lib/api', function() { return { client: { get: jest.fn().mockResolvedValue({ data: {} }), post: jest.fn().mockResolvedValue({ data: {} }) } } })
jest.mock('@/lib/store', function() {
  return { useAppStore: Object.assign(function(sel) { const state = { userProfile: { name: 'Test Officer' }, isAuthenticated: true, clearAuth: jest.fn() }; return typeof sel === 'function' ? sel(state) : state }, { getState: function() { return { userProfile: { name: 'Test Officer' } } }, setState: jest.fn(), subscribe: jest.fn() }) }
})
jest.mock('next/navigation', function() { return { useRouter: function() { return mockRouter }, useSearchParams: function() { return new URLSearchParams() }, useParams: function() { return {} } } })
jest.mock('next/image', function() { return function(props) { return React.createElement('img', props) } })
jest.mock('zustand/react/shallow', function() { return { useShallow: function(fn) { return fn } } })
jest.mock('lucide-react', function() { return new Proxy({}, { get: function() { return function() { return null } } }) })

import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import React from 'react'
import { client } from '@/lib/api'
import OfficerFieldClient from '../app/officer/page'

const mockProfile = {
  id: 'off-001', name: 'Inspector Kumar', phone: '9999911111', email: 'kumar@gcc.in',
  role: 'field_responder', ward_id: 'ward_10', department: 'GCC Roads',
  is_active: true, last_checkin: new Date().toISOString(),
}
const mockIssue = {
  uuid: 'issue-001', issue_type: 'pothole', severity: 4,
  description: 'Deep pothole on Anna Salai', lat: 13.0827, lon: 80.2707,
  road_name: 'Anna Salai', status: 'open', created_at: '2026-06-01T10:00:00Z',
  category: 'roads', ward_name: 'Ward 10', confirmation_count: 3,
  sla_deadline: new Date(Date.now() + 7200000).toISOString(),
  before_photo_url: 'https://example.com/before.jpg',
}

describe('OfficerFieldClient', function() {
  beforeEach(function() { jest.clearAllMocks() })

  it('renders Field Response Uplink heading', function() {
    render(React.createElement(OfficerFieldClient))
    expect(screen.getByText('Field Response Uplink')).toBeTruthy()
  })

  it('renders page structure', function() {
    const { container } = render(React.createElement(OfficerFieldClient))
    expect(container).toBeTruthy()
    expect(container.querySelector('[class*="sv-page"]')).toBeTruthy()
  })

  it('renders with surface card content', function() {
    render(React.createElement(OfficerFieldClient))
    expect(screen.getByText('Field Response Uplink')).toBeTruthy()
  })

  it('renders loading state', function() {
    const { container } = render(React.createElement(OfficerFieldClient))
    expect(container.textContent).toContain('Syncing')
  })

  it('renders without crashing', function() {
    const { container } = render(React.createElement(OfficerFieldClient))
    expect(container.textContent).toContain('Field Response Uplink')
  })

  it('shows unauthorised error and redirects on 401', async function() {
    client.get.mockRejectedValueOnce({ response: { status: 401 } })
    render(React.createElement(OfficerFieldClient))
    await waitFor(function() { expect(screen.getByText(/Unauthorized/i)).toBeTruthy() })
  })

  it('shows generic error message on non-auth failure', async function() {
    client.get.mockRejectedValueOnce(new Error('Network error'))
    render(React.createElement(OfficerFieldClient))
    await waitFor(function() { expect(screen.getByText(/Failed to synchronize/i)).toBeTruthy() })
  })

  it('renders officer name after data loads', async function() {
    client.get.mockResolvedValueOnce({ data: mockProfile })
    client.get.mockResolvedValueOnce({ data: [mockIssue] })
    render(React.createElement(OfficerFieldClient))
    await waitFor(function() { expect(screen.getByText('Inspector Kumar')).toBeTruthy() })
  })

  it('renders officer role badge', async function() {
    client.get.mockResolvedValueOnce({ data: mockProfile })
    client.get.mockResolvedValueOnce({ data: [mockIssue] })
    render(React.createElement(OfficerFieldClient))
    await waitFor(function() { expect(screen.getByText(/field responder/i)).toBeTruthy() })
  })

  it('renders department and ward', async function() {
    client.get.mockResolvedValueOnce({ data: mockProfile })
    client.get.mockResolvedValueOnce({ data: [mockIssue] })
    render(React.createElement(OfficerFieldClient))
    await waitFor(function() { expect(screen.getByText(/GCC Roads/i)).toBeTruthy() })
  })

  it('renders Active Dispatches count', async function() {
    client.get.mockResolvedValueOnce({ data: mockProfile })
    client.get.mockResolvedValueOnce({ data: [mockIssue] })
    render(React.createElement(OfficerFieldClient))
    await waitFor(function() { expect(screen.getByText(/Active Dispatches/)).toBeTruthy() })
  })

  it('renders issue type in workload', async function() {
    client.get.mockResolvedValueOnce({ data: mockProfile })
    client.get.mockResolvedValueOnce({ data: [mockIssue] })
    render(React.createElement(OfficerFieldClient))
    await waitFor(function() { expect(screen.getByText('pothole')).toBeTruthy() })
  })

  it('renders SLA countdown', async function() {
    client.get.mockResolvedValueOnce({ data: mockProfile })
    client.get.mockResolvedValueOnce({ data: [mockIssue] })
    render(React.createElement(OfficerFieldClient))
    await waitFor(function() { expect(screen.getByText(/left/)).toBeTruthy() })
  })

  it('renders confirmation count', async function() {
    client.get.mockResolvedValueOnce({ data: mockProfile })
    client.get.mockResolvedValueOnce({ data: [mockIssue] })
    render(React.createElement(OfficerFieldClient))
    await waitFor(function() { expect(screen.getAllByText(/3 upvotes/).length).toBeGreaterThanOrEqual(1) })
  })

  it('opens issue detail drawer on click', async function() {
    client.get.mockResolvedValueOnce({ data: mockProfile })
    client.get.mockResolvedValueOnce({ data: [mockIssue] })
    render(React.createElement(OfficerFieldClient))
    await waitFor(function() { expect(screen.getByText('pothole')).toBeTruthy() })
    fireEvent.click(screen.getByText('pothole'))
    await waitFor(function() { expect(screen.getByRole('dialog')).toBeTruthy() })
  })

  it('closes drawer on close button click', async function() {
    client.get.mockResolvedValueOnce({ data: mockProfile })
    client.get.mockResolvedValueOnce({ data: [mockIssue] })
    render(React.createElement(OfficerFieldClient))
    await waitFor(function() { expect(screen.getByText('pothole')).toBeTruthy() })
    fireEvent.click(screen.getByText('pothole'))
    await waitFor(function() { expect(screen.getByText(/Close/)).toBeTruthy() })
    fireEvent.click(screen.getByText(/Close/))
    await waitFor(function() { expect(screen.queryByRole('dialog')).toBeNull() })
  })

  it('renders Navigate GPS button in drawer', async function() {
    client.get.mockResolvedValueOnce({ data: mockProfile })
    client.get.mockResolvedValueOnce({ data: [mockIssue] })
    render(React.createElement(OfficerFieldClient))
    await waitFor(function() { expect(screen.getByText('pothole')).toBeTruthy() })
    fireEvent.click(screen.getByText('pothole'))
    await waitFor(function() { expect(screen.getByText(/Navigate GPS/i)).toBeTruthy() })
  })

  it('renders Stand Down button', async function() {
    client.get.mockResolvedValueOnce({ data: mockProfile })
    client.get.mockResolvedValueOnce({ data: [mockIssue] })
    render(React.createElement(OfficerFieldClient))
    await waitFor(function() { expect(screen.getByText('Stand Down')).toBeTruthy() })
  })

  it('renders Broadcast GPS button', async function() {
    client.get.mockResolvedValueOnce({ data: mockProfile })
    client.get.mockResolvedValueOnce({ data: [mockIssue] })
    render(React.createElement(OfficerFieldClient))
    await waitFor(function() { expect(screen.getByText('Broadcast GPS')).toBeTruthy() })
  })

  it('shows empty workload message', async function() {
    client.get.mockResolvedValueOnce({ data: mockProfile })
    client.get.mockResolvedValueOnce({ data: [] })
    render(React.createElement(OfficerFieldClient))
    await waitFor(function() { expect(screen.getByText(/GRID IS ENTIRELY SECURED/i)).toBeTruthy() })
  })
})
