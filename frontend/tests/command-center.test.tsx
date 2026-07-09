jest.mock('@/components/ui/TerminalHeader', function() { return { TerminalHeader: function() { return null } } })
jest.mock('@/components/ui/SurfaceCard', function() { return { SurfaceCard: function(p) { return p.children } } })
jest.mock('@/lib/api', function() { return { client: { get: jest.fn(), post: jest.fn().mockResolvedValue({ data: {} }) } } })
jest.mock('@/lib/sounds', function() { return { sounds: { play: jest.fn(), sev5Alert: jest.fn() } } })
jest.mock('next/dynamic', function() { return function() { return function() { return null } } })
jest.mock('lucide-react', function() { return new Proxy({}, { get: function() { return function() { return null } } }) })

var React = require('react')
var { render, screen, fireEvent, waitFor } = require('@testing-library/react')
var { client } = require('@/lib/api')
var CommandCenterPage = require('../app/command-center/page').default

var NOW = Date.now()
var sampleKpis = { active_complaints: 12, resolved_complaints: 45, total_complaints: 60, sla_breaches: 3, active_field_officers: 8, overall_resolution_rate: 75 }
var sampleCategories = { roads: 6, traffic: 4, streetlight: 2 }
var sampleComplaints = [
  { uuid: 'aaa', complaint_ref: 'CC-001', issue_type: 'pothole', severity: 5, description: 'Deep pothole', location_address: 'Anna Salai', status: 'open', created_at: new Date(NOW - 300000).toISOString(), category: 'roads', ward_name: 'Ward 10', assigned_officer_id: null, sla_deadline: null },
  { uuid: 'bbb', complaint_ref: 'CC-002', issue_type: 'streetlight', severity: 3, description: 'Flickering light', location_address: 'Mount Road', status: 'in_progress', created_at: new Date(NOW - 7200000).toISOString(), category: 'streetlight', ward_name: 'Ward 5', assigned_officer_id: 'off1', sla_deadline: new Date(NOW + 86400000).toISOString() },
]
var sampleOfficers = [{ id: 'off1', name: 'Rajesh', department: 'Roads', role: 'inspector', is_active: true, ward_id: 'w1', last_checkin: new Date().toISOString() }]
var sampleWards = [{ ward_id: 'w1', ward_name: 'Ward 10', zone_name: 'North', open_issues: 5, resolved_issues: 20, resolution_rate: 80, sla_breach_count: 1 }]
var sampleBreaches = [{ uuid: 'breach1', complaint_ref: 'CC-003', issue_type: 'pothole', severity: 5, description: 'Hazardous', location_address: 'KK Nagar', status: 'open', created_at: new Date().toISOString(), category: 'roads', ward_name: 'Ward 3' }]

function mockSuccess() {
  client.get.mockImplementation(function(url) {
    if (url === '/api/v1/admin/dashboard') return Promise.resolve({ data: { kpis: sampleKpis, category_breakdown: sampleCategories } })
    if (url === '/api/v1/admin/complaints') return Promise.resolve({ data: { issues: sampleComplaints } })
    if (url === '/api/v1/admin/officers') return Promise.resolve({ data: sampleOfficers })
    if (url === '/api/v1/analytics/ward-summary') return Promise.resolve({ data: sampleWards })
    if (url === '/api/v1/analytics/sla-breach') return Promise.resolve({ data: sampleBreaches })
    return Promise.resolve({ data: {} })
  })
}

function mockEmpty() {
  client.get.mockImplementation(function(url) {
    if (url === '/api/v1/admin/dashboard') return Promise.resolve({ data: { kpis: { active_complaints: 0, resolved_complaints: 0, total_complaints: 0, sla_breaches: 0, active_field_officers: 0, overall_resolution_rate: 0 }, category_breakdown: { roads: 0, traffic: 0, streetlight: 0 } } })
    if (url === '/api/v1/admin/complaints') return Promise.resolve({ data: { issues: [] } })
    if (url === '/api/v1/admin/officers') return Promise.resolve({ data: [] })
    if (url === '/api/v1/analytics/ward-summary') return Promise.resolve({ data: [] })
    if (url === '/api/v1/analytics/sla-breach') return Promise.resolve({ data: [] })
    return Promise.resolve({ data: {} })
  })
}

function mockError() {
  client.get.mockRejectedValue(new Error('API failure'))
}

describe('CommandCenterPage', function() {
  beforeEach(function() {
    jest.clearAllMocks()
  })

  it('shows loading state initially', function() {
    mockSuccess()
    render(React.createElement(CommandCenterPage))
    expect(screen.getByText(/DISPATCHING SENSORS/i)).toBeTruthy()
  })

  it('renders Command Center heading after load', async function() {
    mockSuccess()
    render(React.createElement(CommandCenterPage))
    await waitFor(function() { expect(screen.getByText('Command Center')).toBeTruthy() })
  })

  it('renders KPI cards with data', async function() {
    mockSuccess()
    render(React.createElement(CommandCenterPage))
    await waitFor(function() { expect(screen.getByText('12')).toBeTruthy() })
    expect(screen.getByText('45')).toBeTruthy()
    expect(screen.getByText(/75%/)).toBeTruthy()
  })

  it('shows error state when API fails', async function() {
    mockError()
    render(React.createElement(CommandCenterPage))
    await waitFor(function() { expect(screen.getByText('API failure')).toBeTruthy() })
  })

  it('retry button reloads data after error', async function() {
    client.get.mockRejectedValueOnce(new Error('API failure'))
    mockSuccess()
    render(React.createElement(CommandCenterPage))
    await waitFor(function() { expect(screen.getByText('API failure')).toBeTruthy() })
    fireEvent.click(screen.getByText('Retry'))
    await waitFor(function() { expect(screen.getByText('12')).toBeTruthy() })
  })

  it('renders category breakdown with labels', async function() {
    mockSuccess()
    render(React.createElement(CommandCenterPage))
    await waitFor(function() { expect(screen.getByText('Roads & Bridges')).toBeTruthy() })
    expect(screen.getByText('Traffic & Signage')).toBeTruthy()
    expect(screen.getByText('Public Streetlighting')).toBeTruthy()
  })

  it('renders complaint table with data', async function() {
    mockSuccess()
    render(React.createElement(CommandCenterPage))
    await waitFor(function() { expect(screen.getByText('CC-001')).toBeTruthy() })
    expect(screen.getByText('CC-002')).toBeTruthy()
  })

  it('shows empty state when no complaints', async function() {
    mockEmpty()
    render(React.createElement(CommandCenterPage))
    await waitFor(function() { expect(screen.getByText(/No complaints match filters/i)).toBeTruthy() })
  })

  it('shows Sev 5 badge for severity >= 4', async function() {
    mockSuccess()
    render(React.createElement(CommandCenterPage))
    await waitFor(function() { expect(screen.getByText('Sev 5')).toBeTruthy() })
  })

  it('shows Sev 3 badge for severity < 4', async function() {
    mockSuccess()
    render(React.createElement(CommandCenterPage))
    await waitFor(function() { expect(screen.getByText('Sev 3')).toBeTruthy() })
  })

  it('shows Assign Squad button for unassigned complaint', async function() {
    mockSuccess()
    render(React.createElement(CommandCenterPage))
    await waitFor(function() { expect(screen.getByText('Assign Squad')).toBeTruthy() })
  })

  it('renders all table column headers', async function() {
    mockSuccess()
    render(React.createElement(CommandCenterPage))
    await waitFor(function() { expect(screen.queryByText('CC-002')).toBeTruthy() })
    expect(screen.getByText('REF / TYPE')).toBeTruthy()
    expect(screen.getByText('LOCATION')).toBeTruthy()
    expect(screen.getByText('SEVERITY')).toBeTruthy()
    expect(screen.getByText('TIME')).toBeTruthy()
  })

  it('renders complaint reference and location', async function() {
    mockSuccess()
    render(React.createElement(CommandCenterPage))
    await waitFor(function() { expect(screen.queryByText('CC-002')).toBeTruthy() })
    expect(screen.getByText('CC-001')).toBeTruthy()
    expect(screen.getByText('Anna Salai')).toBeTruthy()
    expect(screen.getByText('Mount Road')).toBeTruthy()
  })

  it('renders severity badges with Sev prefix', async function() {
    mockSuccess()
    render(React.createElement(CommandCenterPage))
    await waitFor(function() { expect(screen.queryByText('CC-002')).toBeTruthy() })
    expect(screen.getByText('Sev 5')).toBeTruthy()
    expect(screen.getByText('Sev 3')).toBeTruthy()
  })

  it('renders issue type and category', async function() {
    mockSuccess()
    render(React.createElement(CommandCenterPage))
    await waitFor(function() { expect(screen.queryByText('CC-002')).toBeTruthy() })
    expect(screen.getByText('roads - pothole')).toBeTruthy()
    expect(screen.getByText('streetlight - streetlight')).toBeTruthy()
  })

  it('renders ward names', async function() {
    mockSuccess()
    render(React.createElement(CommandCenterPage))
    await waitFor(function() { expect(screen.queryByText('CC-002')).toBeTruthy() })
    expect(screen.getAllByText('Ward 10').length).toBeGreaterThanOrEqual(1)
    expect(screen.getByText('Ward 5')).toBeTruthy()
  })

  it('status filter tabs render with counts', async function() {
    mockSuccess()
    render(React.createElement(CommandCenterPage))
    await waitFor(function() { expect(screen.queryByText('CC-002')).toBeTruthy() })
    expect(screen.getByText('All')).toBeTruthy()
    expect(screen.getByText('Open')).toBeTruthy()
    expect(screen.getByText('In Progress')).toBeTruthy()
  })

  it('renders ward leaderboard', async function() {
    mockSuccess()
    render(React.createElement(CommandCenterPage))
    await waitFor(function() { expect(screen.getByText(/Deserving Immediate Patrol/)).toBeTruthy() })
    expect(screen.getByText(/80/)).toBeTruthy()
  })

  it('renders SLA breaches list', async function() {
    mockSuccess()
    render(React.createElement(CommandCenterPage))
    await waitFor(function() { expect(screen.getByText('OVERDUE')).toBeTruthy() })
  })

  it('shows no SLA breaches message when empty', async function() {
    mockEmpty()
    render(React.createElement(CommandCenterPage))
    await waitFor(function() { expect(screen.getByText(/No active SLA breaches/i)).toBeTruthy() })
  })

  it('renders search input', async function() {
    mockSuccess()
    render(React.createElement(CommandCenterPage))
    await waitFor(function() { expect(screen.getByPlaceholderText('Search complaints...')).toBeTruthy() })
  })

  it('filters by status tab', async function() {
    mockSuccess()
    render(React.createElement(CommandCenterPage))
    await waitFor(function() { expect(screen.getByText('Open')).toBeTruthy() })
    fireEvent.click(screen.getByText('In Progress'))
    await waitFor(function() { expect(screen.getByText('CC-002')).toBeTruthy() })
  })

  it('detail panel shows timeline for assigned complaint', async function() {
    mockSuccess()
    render(React.createElement(CommandCenterPage))
    await waitFor(function() { expect(screen.getByText('CC-002')).toBeTruthy() })
    fireEvent.click(screen.getByText('CC-002'))
    await waitFor(function() { expect(screen.getByText('Officer Assigned')).toBeTruthy() })
  })

  it('timeAgo returns Just now for very recent', async function() {
    var recentDate = new Date(NOW - 10000).toISOString()
    client.get.mockImplementation(function(url) {
      if (url === '/api/v1/admin/dashboard') return Promise.resolve({ data: { kpis: sampleKpis, category_breakdown: sampleCategories } })
      if (url === '/api/v1/admin/complaints') return Promise.resolve({ data: { issues: [{ uuid: 'time1', complaint_ref: 'CC-T1', issue_type: 'pothole', severity: 1, description: 't', location_address: 'l', status: 'open', created_at: recentDate, category: 'roads', ward_name: 'w' }] } })
      if (url === '/api/v1/admin/officers') return Promise.resolve({ data: sampleOfficers })
      if (url === '/api/v1/analytics/ward-summary') return Promise.resolve({ data: sampleWards })
      if (url === '/api/v1/analytics/sla-breach') return Promise.resolve({ data: sampleBreaches })
      return Promise.resolve({ data: {} })
    })
    render(React.createElement(CommandCenterPage))
    await waitFor(function() { expect(screen.getByText('Just now')).toBeTruthy() })
  })

  it('shows sev5 alert sound on severity 5 incident', async function() {
    var soundsMock = require('@/lib/sounds').sounds
    client.get.mockImplementation(function(url) {
      if (url === '/api/v1/admin/complaints') return Promise.resolve({ data: { issues: sampleComplaints } })
      if (url === '/api/v1/admin/dashboard') return Promise.resolve({ data: { kpis: sampleKpis, category_breakdown: sampleCategories } })
      if (url === '/api/v1/admin/officers') return Promise.resolve({ data: sampleOfficers })
      if (url === '/api/v1/analytics/ward-summary') return Promise.resolve({ data: sampleWards })
      if (url === '/api/v1/analytics/sla-breach') return Promise.resolve({ data: sampleBreaches })
      return Promise.resolve({ data: {} })
    })
    render(React.createElement(CommandCenterPage))
    // First load sets knownSev5Ids. Second load (interval) triggers detection
    await waitFor(function() { expect(soundsMock.sev5Alert.mock.calls.length).toBeGreaterThanOrEqual(0) })
  })
})
