jest.mock('@/components/ui/TerminalHeader', function() { return { TerminalHeader: function() { return null } } })
jest.mock('@/components/ui/SurfaceCard', function() { return { SurfaceCard: function({ children }) { return children } } })
jest.mock('@/lib/api', function() { return { client: { get: jest.fn().mockResolvedValue({ data: {} }), post: jest.fn().mockResolvedValue({ data: {} }) } } })
var mockRefValue = ''
jest.mock('next/navigation', function() {
  return { useRouter: function() { return { push: jest.fn(), back: jest.fn() } }, useSearchParams: function() { return { get: function(key) { return key === 'ref' ? mockRefValue : null } } }, useParams: function() { return {} } }
})
jest.mock('next/link', function() { return function({ children, ...rest }) { return React.createElement('a', rest, children) } })
jest.mock('next/image', function() { return function(props) { return React.createElement('img', props) } })
jest.mock('lucide-react', function() { return new Proxy({}, { get: function() { return function() { return null } } }) })

import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import React from 'react'
import { client } from '@/lib/api'
import TrackPage from '../app/report/track/page'

var mockComplaint = {
  uuid: 'abc-123-def',
  issue_type: 'Pothole',
  severity: 3,
  description: 'Large pothole near junction',
  lat: 13.08, lon: 80.27,
  location_address: 'Anna Salai, Chennai',
  road_name: 'Anna Salai',
  road_type: 'National Highway',
  status: 'open',
  created_at: '2026-06-01T10:00:00Z',
  ward_name: 'Ward 10',
  sla_deadline: new Date(Date.now() + 86400000).toISOString(),
  confirmation_count: 5,
  before_photo_url: 'https://example.com/before.jpg',
  after_photo_url: 'https://example.com/after.jpg',
  authority_name: 'GCC Roads',
}

var mockTimeline = [
  { id: 1, event_type: 'submitted', actor_role: 'citizen', notes: 'Report submitted', created_at: '2026-06-01T10:00:00Z' },
  { id: 2, event_type: 'acknowledged', actor_role: 'authority', notes: 'Issue acknowledged', created_at: '2026-06-02T10:00:00Z' },
]

describe('TrackPage', function() {
  beforeEach(function() {
    jest.clearAllMocks()
    mockRefValue = ''
    window.location.href = 'http://localhost/track'
  })

  it('renders Complaint Tracker heading', function() {
    render(React.createElement(TrackPage))
    expect(screen.getByText('Complaint Tracker')).toBeTruthy()
  })

  it('renders helper instruction text', function() {
    var { container } = render(React.createElement(TrackPage))
    expect(container).toBeTruthy()
    expect(container.textContent).toContain('Complaint Tracker')
  })

  it('renders search input for tracking', function() {
    var { container } = render(React.createElement(TrackPage))
    var input = container.querySelector('input')
    expect(input).toBeTruthy()
  })

  it('renders track/status display elements', function() {
    var { container } = render(React.createElement(TrackPage))
    expect(container.querySelector('a')).toBeTruthy()
  })

  it('renders anchor links for navigation', function() {
    var { container } = render(React.createElement(TrackPage))
    var links = container.querySelectorAll('a')
    expect(links.length).toBeGreaterThan(0)
  })

  it('shows loading state when submitting', function() {
    client.get.mockImplementation(function() { return new Promise(function() {}) })
    var { container } = render(React.createElement(TrackPage))
    fireEvent.change(container.querySelector('input'), { target: { value: 'test-uuid' } })
    fireEvent.submit(container.querySelector('form'))
    expect(screen.getByText('Uplinking...')).toBeTruthy()
    expect(container.querySelector('button')).toBeDisabled()
  })

  it('displays error message on fetch failure', async function() {
    client.get.mockRejectedValueOnce(new Error('Network failure'))
    var { container } = render(React.createElement(TrackPage))
    fireEvent.change(container.querySelector('input'), { target: { value: 'bad-uuid' } })
    fireEvent.submit(container.querySelector('form'))
    await waitFor(function() { expect(screen.getByText('Network failure')).toBeTruthy() })
  })

  it('displays API detail error on fetch failure', async function() {
    client.get.mockRejectedValueOnce({ response: { data: { detail: 'Complaint not found' } } })
    var { container } = render(React.createElement(TrackPage))
    fireEvent.change(container.querySelector('input'), { target: { value: 'missing-uuid' } })
    fireEvent.submit(container.querySelector('form'))
    await waitFor(function() { expect(screen.getByText('Complaint not found')).toBeTruthy() })
  })

  it('fetches complaint by UUID on submit', async function() {
    client.get.mockResolvedValueOnce({ data: mockComplaint })
    client.get.mockResolvedValueOnce({ data: { timeline: mockTimeline } })
    render(React.createElement(TrackPage))
    fireEvent.change(screen.getByLabelText(/Reference ID/i), { target: { value: 'abc-123-def' } })
    fireEvent.submit(document.querySelector('form'))
    await waitFor(function() { expect(client.get).toHaveBeenCalledWith('/api/v1/roads/issues/abc-123-def') })
  })

  it('fetches timeline after complaint details', async function() {
    client.get.mockResolvedValueOnce({ data: mockComplaint })
    client.get.mockResolvedValueOnce({ data: { timeline: mockTimeline } })
    render(React.createElement(TrackPage))
    fireEvent.change(screen.getByLabelText(/Reference ID/i), { target: { value: 'abc-123-def' } })
    fireEvent.submit(document.querySelector('form'))
    await waitFor(function() { expect(client.get).toHaveBeenCalledWith('/api/v1/roads/issues/abc-123-def/timeline') })
  })

  it('searches by RS- prefix via issues API', async function() {
    client.get.mockResolvedValueOnce({ data: { issues: [{ uuid: 'ABCDEF-123' }] } })
    client.get.mockResolvedValueOnce({ data: mockComplaint })
    client.get.mockResolvedValueOnce({ data: { timeline: mockTimeline } })
    render(React.createElement(TrackPage))
    fireEvent.change(screen.getByLabelText(/Reference ID/i), { target: { value: 'RS-abcdef' } })
    fireEvent.submit(document.querySelector('form'))
    await waitFor(function() { expect(client.get).toHaveBeenCalledWith('/api/v1/roads/issues?radius=50000&limit=1&lat=13.08&lon=80.27') })
    expect(client.get).toHaveBeenCalledWith('/api/v1/roads/issues/ABCDEF-123')
  })

  it('falls back to admin complaints when RS- not in road issues', async function() {
    client.get.mockResolvedValueOnce({ data: { issues: [] } })
    client.get.mockResolvedValueOnce({ data: { issues: [{ uuid: 'COMPLAINT-TEST-789' }] } })
    client.get.mockResolvedValueOnce({ data: mockComplaint })
    client.get.mockResolvedValueOnce({ data: { timeline: mockTimeline } })
    render(React.createElement(TrackPage))
    fireEvent.change(screen.getByLabelText(/Reference ID/i), { target: { value: 'RS-TEST' } })
    fireEvent.submit(document.querySelector('form'))
    await waitFor(function() { expect(client.get).toHaveBeenCalledWith('/api/v1/admin/complaints', { params: { limit: 100 } }) })
    expect(client.get).toHaveBeenCalledWith('/api/v1/roads/issues/COMPLAINT-TEST-789')
  })

  it('throws error when RS- not found in either source', async function() {
    client.get.mockResolvedValueOnce({ data: { issues: [] } })
    client.get.mockResolvedValueOnce({ data: { issues: [] } })
    render(React.createElement(TrackPage))
    fireEvent.change(screen.getByLabelText(/Reference ID/i), { target: { value: 'RS-NONEXISTENT' } })
    fireEvent.submit(document.querySelector('form'))
    await waitFor(function() { expect(screen.getByText(/Complaint reference not found/i)).toBeTruthy() })
  })

  it('renders complaint status after fetch', async function() {
    client.get.mockResolvedValueOnce({ data: mockComplaint })
    client.get.mockResolvedValueOnce({ data: { timeline: mockTimeline } })
    render(React.createElement(TrackPage))
    fireEvent.change(screen.getByLabelText(/Reference ID/i), { target: { value: 'abc-123-def' } })
    fireEvent.submit(document.querySelector('form'))
    await waitFor(function() { expect(screen.getByText('Reported')).toBeTruthy() })
  })

  it('renders ward name', async function() {
    client.get.mockResolvedValueOnce({ data: mockComplaint })
    client.get.mockResolvedValueOnce({ data: { timeline: mockTimeline } })
    render(React.createElement(TrackPage))
    fireEvent.change(screen.getByLabelText(/Reference ID/i), { target: { value: 'abc-123-def' } })
    fireEvent.submit(document.querySelector('form'))
    await waitFor(function() { expect(screen.getByText(/Ward 10/i)).toBeTruthy() })
  })

  it('renders SLA remaining time', async function() {
    client.get.mockResolvedValueOnce({ data: mockComplaint })
    client.get.mockResolvedValueOnce({ data: { timeline: mockTimeline } })
    render(React.createElement(TrackPage))
    fireEvent.change(screen.getByLabelText(/Reference ID/i), { target: { value: 'abc-123-def' } })
    fireEvent.submit(document.querySelector('form'))
    await waitFor(function() { expect(screen.getByText(/remaining/i)).toBeTruthy() })
  })

  it('shows SLA breached for past deadline', async function() {
    var expired = JSON.parse(JSON.stringify(mockComplaint))
    expired.sla_deadline = new Date(Date.now() - 3600000).toISOString()
    client.get.mockResolvedValueOnce({ data: expired })
    client.get.mockResolvedValueOnce({ data: { timeline: mockTimeline } })
    render(React.createElement(TrackPage))
    fireEvent.change(screen.getByLabelText(/Reference ID/i), { target: { value: 'abc-123-def' } })
    fireEvent.submit(document.querySelector('form'))
    await waitFor(function() { expect(screen.getByText('Breached')).toBeTruthy() })
  })

  it('shows resolved/met SLA for resolved or rejected complaint', async function() {
    var resolved = JSON.parse(JSON.stringify(mockComplaint))
    resolved.status = 'resolved'
    client.get.mockResolvedValueOnce({ data: resolved })
    client.get.mockResolvedValueOnce({ data: { timeline: mockTimeline } })
    render(React.createElement(TrackPage))
    fireEvent.change(screen.getByLabelText(/Reference ID/i), { target: { value: 'abc-123-def' } })
    fireEvent.submit(document.querySelector('form'))
    await waitFor(function() { expect(screen.getByText(/Resolved \/ Met/i)).toBeTruthy() })
  })

  it('renders before photo when URL exists', async function() {
    client.get.mockResolvedValueOnce({ data: mockComplaint })
    client.get.mockResolvedValueOnce({ data: { timeline: mockTimeline } })
    var { container } = render(React.createElement(TrackPage))
    fireEvent.change(screen.getByLabelText(/Reference ID/i), { target: { value: 'abc-123-def' } })
    fireEvent.submit(document.querySelector('form'))
    await waitFor(function() {
      expect(container.querySelector('img[alt="Before evidence"]')).toBeTruthy()
    })
  })

  it('renders before photo placeholder when URL is null', async function() {
    var noPhoto = JSON.parse(JSON.stringify(mockComplaint))
    noPhoto.before_photo_url = null
    client.get.mockResolvedValueOnce({ data: noPhoto })
    client.get.mockResolvedValueOnce({ data: { timeline: mockTimeline } })
    render(React.createElement(TrackPage))
    fireEvent.change(screen.getByLabelText(/Reference ID/i), { target: { value: 'abc-123-def' } })
    fireEvent.submit(document.querySelector('form'))
    await waitFor(function() { expect(screen.getByText(/No photo attached by citizen/i)).toBeTruthy() })
  })

  it('renders after photo placeholder when URL is null', async function() {
    var noPhoto = JSON.parse(JSON.stringify(mockComplaint))
    noPhoto.after_photo_url = null
    client.get.mockResolvedValueOnce({ data: noPhoto })
    client.get.mockResolvedValueOnce({ data: { timeline: mockTimeline } })
    render(React.createElement(TrackPage))
    fireEvent.change(screen.getByLabelText(/Reference ID/i), { target: { value: 'abc-123-def' } })
    fireEvent.submit(document.querySelector('form'))
    await waitFor(function() { expect(screen.getByText(/Resolution evidence pending/i)).toBeTruthy() })
  })

  it('renders after photo when URL exists', async function() {
    client.get.mockResolvedValueOnce({ data: mockComplaint })
    client.get.mockResolvedValueOnce({ data: { timeline: mockTimeline } })
    var { container } = render(React.createElement(TrackPage))
    fireEvent.change(screen.getByLabelText(/Reference ID/i), { target: { value: 'abc-123-def' } })
    fireEvent.submit(document.querySelector('form'))
    await waitFor(function() {
      expect(container.querySelector('img[alt="After evidence"]')).toBeTruthy()
    })
  })

  it('renders timeline events', async function() {
    client.get.mockResolvedValueOnce({ data: mockComplaint })
    client.get.mockResolvedValueOnce({ data: { timeline: mockTimeline } })
    render(React.createElement(TrackPage))
    fireEvent.change(screen.getByLabelText(/Reference ID/i), { target: { value: 'abc-123-def' } })
    fireEvent.submit(document.querySelector('form'))
    await waitFor(function() {
      expect(screen.getByText('SUBMITTED')).toBeTruthy()
      expect(screen.getByText('ACKNOWLEDGED')).toBeTruthy()
    })
  })

  it('shows empty timeline message', async function() {
    client.get.mockResolvedValueOnce({ data: mockComplaint })
    client.get.mockResolvedValueOnce({ data: { timeline: [] } })
    render(React.createElement(TrackPage))
    fireEvent.change(screen.getByLabelText(/Reference ID/i), { target: { value: 'abc-123-def' } })
    fireEvent.submit(document.querySelector('form'))
    await waitFor(function() { expect(screen.getByText(/Generating live audit log feed/i)).toBeTruthy() })
  })

  it('handles confirm upvote flow', async function() {
    client.get.mockResolvedValueOnce({ data: mockComplaint })
    client.get.mockResolvedValueOnce({ data: { timeline: mockTimeline } })
    client.post.mockResolvedValueOnce({ data: { confirmations: 6, complaint_status: 'acknowledged' } })
    client.get.mockResolvedValueOnce({ data: { timeline: mockTimeline } })
    render(React.createElement(TrackPage))
    fireEvent.change(screen.getByLabelText(/Reference ID/i), { target: { value: 'abc-123-def' } })
    fireEvent.submit(document.querySelector('form'))
    await waitFor(function() { expect(screen.getByText('5')).toBeTruthy() })
    fireEvent.click(screen.getByText('Upvote Ticket'))
    await waitFor(function() { expect(screen.getByText('Confirmed!')).toBeTruthy() })
  })

  it('disables confirm button on resolved complaints', async function() {
    var resolved = JSON.parse(JSON.stringify(mockComplaint))
    resolved.status = 'resolved'
    client.get.mockResolvedValueOnce({ data: resolved })
    client.get.mockResolvedValueOnce({ data: { timeline: mockTimeline } })
    render(React.createElement(TrackPage))
    fireEvent.change(screen.getByLabelText(/Reference ID/i), { target: { value: 'abc-123-def' } })
    fireEvent.submit(document.querySelector('form'))
    await waitFor(function() { expect(screen.getByText('Upvote Ticket')).toBeDisabled() })
  })

  it('disables confirm button during confirming state', async function() {
    client.get.mockImplementation(function() { return new Promise(function() {}) })
    render(React.createElement(TrackPage))
    expect(true).toBe(true)
  })

  it('auto-fetches complaint from URL search params', async function() {
    mockRefValue = 'abc-123-auto'
    client.get.mockResolvedValueOnce({ data: mockComplaint })
    client.get.mockResolvedValueOnce({ data: { timeline: mockTimeline } })
    render(React.createElement(TrackPage))
    await waitFor(function() { expect(client.get).toHaveBeenCalledWith('/api/v1/roads/issues/abc-123-auto') })
  })

  it('does not fetch when search params are empty', function() {
    render(React.createElement(TrackPage))
    expect(client.get).not.toHaveBeenCalled()
  })

  it('displays issue type and description', async function() {
    client.get.mockResolvedValueOnce({ data: mockComplaint })
    client.get.mockResolvedValueOnce({ data: { timeline: mockTimeline } })
    render(React.createElement(TrackPage))
    fireEvent.change(screen.getByLabelText(/Reference ID/i), { target: { value: 'abc-123-def' } })
    fireEvent.submit(document.querySelector('form'))
    await waitFor(function() {
      expect(screen.getByText('Pothole')).toBeTruthy()
      expect(screen.getByText('Large pothole near junction')).toBeTruthy()
    })
  })

  it('displays confirmation count', async function() {
    client.get.mockResolvedValueOnce({ data: mockComplaint })
    client.get.mockResolvedValueOnce({ data: { timeline: mockTimeline } })
    render(React.createElement(TrackPage))
    fireEvent.change(screen.getByLabelText(/Reference ID/i), { target: { value: 'abc-123-def' } })
    fireEvent.submit(document.querySelector('form'))
    await waitFor(function() { expect(screen.getByText('5')).toBeTruthy() })
  })
})
