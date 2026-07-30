jest.mock('@/hooks/usePageEntry', function() { return { usePageEntry: function() { return { current: null } } } })
jest.mock('@/lib/api', function() { return { fetchNearbyServices: jest.fn().mockResolvedValue({ services: [] }), submitReport: jest.fn().mockResolvedValue({}) } })
jest.mock('lucide-react', function() { return new Proxy({}, { get: function() { return function() { return null } } }) })

import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import React from 'react'
import { fetchNearbyServices, submitReport } from '@/lib/api'
import BystanderModePage from '../app/bystander/page'

let mockGetCurrentPosition = jest.fn()

describe('BystanderModePage', function() {
  beforeEach(function() {
    jest.clearAllMocks()
    mockGetCurrentPosition = jest.fn()
    Object.defineProperty(global.navigator, 'geolocation', {
      value: { getCurrentPosition: mockGetCurrentPosition },
      writable: true, configurable: true,
    })
  })

  it('renders I Witnessed heading', function() {
    render(React.createElement(BystanderModePage))
    expect(screen.getByText('I Witnessed')).toBeTruthy()
  })

  it('renders Bystander Mode label and An Accident text', function() {
    render(React.createElement(BystanderModePage))
    expect(screen.getByText('Bystander Mode')).toBeTruthy()
    expect(screen.getByText('An Accident')).toBeTruthy()
  })

  it('renders description text', function() {
    render(React.createElement(BystanderModePage))
    expect(screen.getByText(/SafeVixAI will capture your location/)).toBeTruthy()
  })

  it('renders Activate Bystander Mode button', function() {
    render(React.createElement(BystanderModePage))
    expect(screen.getByText('Activate Bystander Mode')).toBeTruthy()
  })

  it('renders footer note about offline and no login', function() {
    render(React.createElement(BystanderModePage))
    expect(screen.getByText(/No login required/)).toBeTruthy()
  })

  it('shows GPS loading phase on button click', function() {
    render(React.createElement(BystanderModePage))
    fireEvent.click(screen.getByText('Activate Bystander Mode'))
    expect(screen.getByText(/Capturing Location/i)).toBeTruthy()
  })

  it('transitions to steps on GPS success', async function() {
    mockGetCurrentPosition.mockImplementation(function(success) { success({ coords: { latitude: 13.0827, longitude: 80.2707 } }) })
    render(React.createElement(BystanderModePage))
    fireEvent.click(screen.getByText('Activate Bystander Mode'))
    await waitFor(function() { expect(screen.getByText(/Bystander Protocol Active/i)).toBeTruthy() })
  })

  it('submits accident report on GPS success', async function() {
    mockGetCurrentPosition.mockImplementation(function(success) { success({ coords: { latitude: 13.0827, longitude: 80.2707 } }) })
    render(React.createElement(BystanderModePage))
    fireEvent.click(screen.getByText('Activate Bystander Mode'))
    await waitFor(function() { expect(submitReport).toHaveBeenCalledWith(expect.objectContaining({ issue_type: 'accident', severity: 4 })) })
  })

  it('fetches nearest hospital after accident report', async function() {
    mockGetCurrentPosition.mockImplementation(function(success) { success({ coords: { latitude: 13.0827, longitude: 80.2707 } }) })
    fetchNearbyServices.mockResolvedValue({ services: [{ name: 'Apollo Hospital', distanceMeters: 3200 }] })
    render(React.createElement(BystanderModePage))
    fireEvent.click(screen.getByText('Activate Bystander Mode'))
    await waitFor(function() { expect(screen.getByText(/Apollo Hospital/i)).toBeTruthy() })
  })

  it('shows Reported badge when accident report succeeds', async function() {
    mockGetCurrentPosition.mockImplementation(function(success) { success({ coords: { latitude: 13.0827, longitude: 80.2707 } }) })
    render(React.createElement(BystanderModePage))
    fireEvent.click(screen.getByText('Activate Bystander Mode'))
    await waitFor(function() { expect(screen.getByText('Reported')).toBeTruthy() })
  })

  it('shows GPS error badge when geolocation fails', async function() {
    mockGetCurrentPosition.mockImplementation(function(success, error) { error({ message: 'Permission denied' }) })
    render(React.createElement(BystanderModePage))
    fireEvent.click(screen.getByText('Activate Bystander Mode'))
    await waitFor(function() { expect(screen.getByText(/GPS error: Permission denied/i)).toBeTruthy() })
  })

  it('shows steps screen even on GPS error', async function() {
    mockGetCurrentPosition.mockImplementation(function(success, error) { error({ message: 'Timeout' }) })
    render(React.createElement(BystanderModePage))
    fireEvent.click(screen.getByText('Activate Bystander Mode'))
    await waitFor(function() { expect(screen.getByText(/Bystander Protocol Active/i)).toBeTruthy() })
  })

  it('shows steps when geolocation is unavailable', function() {
    Object.defineProperty(global.navigator, 'geolocation', { value: undefined, writable: true, configurable: true })
    render(React.createElement(BystanderModePage))
    fireEvent.click(screen.getByText('Activate Bystander Mode'))
    expect(screen.getByText(/Bystander Protocol Active/i)).toBeTruthy()
  })

  it('renders first aid steps after GPS success', async function() {
    mockGetCurrentPosition.mockImplementation(function(success) { success({ coords: { latitude: 13.0827, longitude: 80.2707 } }) })
    render(React.createElement(BystanderModePage))
    fireEvent.click(screen.getByText('Activate Bystander Mode'))
    await waitFor(function() { expect(screen.getByText(/STOP your vehicle safely/i)).toBeTruthy() })
  })

  it('toggles step completion on click', async function() {
    mockGetCurrentPosition.mockImplementation(function(success) { success({ coords: { latitude: 13.0827, longitude: 80.2707 } }) })
    render(React.createElement(BystanderModePage))
    fireEvent.click(screen.getByText('Activate Bystander Mode'))
    await waitFor(function() { expect(screen.getByText(/STOP your vehicle safely/i)).toBeTruthy() })
    fireEvent.click(screen.getByText(/STOP your vehicle safely/i))
    await waitFor(function() { expect(screen.getByText('1/8 done')).toBeTruthy() })
    fireEvent.click(screen.getByText(/STOP your vehicle safely/i))
    await waitFor(function() { expect(screen.getByText('0/8 done')).toBeTruthy() })
  })

  it('shows critical badge on critical steps', async function() {
    mockGetCurrentPosition.mockImplementation(function(success) { success({ coords: { latitude: 13.0827, longitude: 80.2707 } }) })
    render(React.createElement(BystanderModePage))
    fireEvent.click(screen.getByText('Activate Bystander Mode'))
    await waitFor(function() { expect(screen.getAllByText('Critical').length).toBeGreaterThanOrEqual(3) })
  })

  it('shows all steps done screen when all completed', async function() {
    mockGetCurrentPosition.mockImplementation(function(success) { success({ coords: { latitude: 13.0827, longitude: 80.2707 } }) })
    render(React.createElement(BystanderModePage))
    fireEvent.click(screen.getByText('Activate Bystander Mode'))
    await waitFor(function() { expect(screen.getByText(/STOP your vehicle safely/i)).toBeTruthy() })
    const buttons = screen.getAllByRole('button')
    buttons.forEach(function(b) { fireEvent.click(b) })
    await waitFor(function() { expect(screen.getByText('All Steps Done')).toBeTruthy() })
  })

  it('renders Call 108 button on steps screen', async function() {
    mockGetCurrentPosition.mockImplementation(function(success) { success({ coords: { latitude: 13.0827, longitude: 80.2707 } }) })
    render(React.createElement(BystanderModePage))
    fireEvent.click(screen.getByText('Activate Bystander Mode'))
    await waitFor(function() { expect(screen.getByText('Call 108')).toBeTruthy() })
  })

  it('renders Call 108 Again on done screen', async function() {
    mockGetCurrentPosition.mockImplementation(function(success) { success({ coords: { latitude: 13.0827, longitude: 80.2707 } }) })
    render(React.createElement(BystanderModePage))
    fireEvent.click(screen.getByText('Activate Bystander Mode'))
    await waitFor(function() { expect(screen.getByText(/STOP your vehicle safely/i)).toBeTruthy() })
    screen.getAllByRole('button').forEach(function(b) { fireEvent.click(b) })
    await waitFor(function() { expect(screen.getByText(/Call 108 Again/i)).toBeTruthy() })
  })

  it('renders Show Location on Maps on done screen with GPS', async function() {
    mockGetCurrentPosition.mockImplementation(function(success) { success({ coords: { latitude: 13.0827, longitude: 80.2707 } }) })
    render(React.createElement(BystanderModePage))
    fireEvent.click(screen.getByText('Activate Bystander Mode'))
    await waitFor(function() { expect(screen.getByText(/STOP your vehicle safely/i)).toBeTruthy() })
    screen.getAllByRole('button').forEach(function(b) { fireEvent.click(b) })
    await waitFor(function() { expect(screen.getByText(/Show Location on Maps/i)).toBeTruthy() })
  })

  it('omits map link on done screen when no GPS', async function() {
    mockGetCurrentPosition.mockImplementation(function(success, error) { error({ message: 'No signal' }) })
    render(React.createElement(BystanderModePage))
    fireEvent.click(screen.getByText('Activate Bystander Mode'))
    await waitFor(function() { expect(screen.getByText(/Bystander Protocol Active/i)).toBeTruthy() })
    screen.getAllByRole('button').forEach(function(b) { fireEvent.click(b) })
    await waitFor(function() { expect(screen.getByText(/Call 108 Again/i)).toBeTruthy() })
    expect(screen.queryByText(/Show Location on Maps/i)).toBeNull()
  })
})
