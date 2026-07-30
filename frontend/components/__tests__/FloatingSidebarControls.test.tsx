jest.mock('@gsap/react', function() { return { useGSAP: jest.fn() } })
const mockPush = jest.fn()
jest.mock('next/navigation', function() { return { useRouter: function() { return { push: mockPush } }, usePathname: function() { return '/' }, useSearchParams: function() { return new URLSearchParams() } } })

import { render, screen, fireEvent } from '@testing-library/react'
import React from 'react'
import FloatingSidebarControls from '../dashboard/FloatingSidebarControls'

const mockStore: Record<string, any> = {
  drivingScore: 78,
  showHazardHeatmap: false,
  showSatellite: false,
  showTraffic: false,
  showSafeSpaces: true,
  showEmergencyServices: true,
  setShowHazardHeatmap: jest.fn(),
  setShowSatellite: jest.fn(),
  setShowTraffic: jest.fn(),
  setShowSafeSpaces: jest.fn(),
  setShowEmergencyServices: jest.fn(),
}

jest.mock('@/lib/store', function() {
  return {
    useAppStore: jest.fn(function(selector: any) { return typeof selector === 'function' ? selector(mockStore) : mockStore }),
  }
})

describe('FloatingSidebarControls', function() {
  beforeEach(function() {
    jest.clearAllMocks()
  })

  it('renders SOS button', function() {
    render(React.createElement(FloatingSidebarControls))
    expect(screen.getByText('SOS')).toBeInTheDocument()
  })

  it('renders driving score gauge', function() {
    render(React.createElement(FloatingSidebarControls))
    expect(screen.getByText('78')).toBeInTheDocument()
  })

  it('renders layers button', function() {
    render(React.createElement(FloatingSidebarControls))
    expect(screen.getByLabelText(/Map Layers/)).toBeInTheDocument()
  })

  it('opens layer menu on layers button click', function() {
    render(React.createElement(FloatingSidebarControls))
    fireEvent.click(screen.getByLabelText(/Map Layers/))
    expect(screen.getByText('Satellite')).toBeInTheDocument()
    expect(screen.getByText('Traffic')).toBeInTheDocument()
    expect(screen.getByText('Safe Spaces')).toBeInTheDocument()
    expect(screen.getByText('Hazard Heatmap')).toBeInTheDocument()
    expect(screen.getByText('Emergency Services')).toBeInTheDocument()
  })

  it('closes layer menu on close button', function() {
    render(React.createElement(FloatingSidebarControls))
    fireEvent.click(screen.getByLabelText(/Map Layers/))
    expect(screen.getByText('Satellite')).toBeInTheDocument()
    fireEvent.click(screen.getByLabelText('Close layer menu'))
    expect(screen.queryByText('Satellite')).not.toBeInTheDocument()
  })

  it('shows active layer count badge', function() {
    render(React.createElement(FloatingSidebarControls))
    expect(screen.getByText('2')).toBeInTheDocument()
  })

  it('shows relocate button', function() {
    render(React.createElement(FloatingSidebarControls))
    expect(screen.getByLabelText(/Re-center map/)).toBeInTheDocument()
  })

  it('shows emergency protocols button', function() {
    render(React.createElement(FloatingSidebarControls))
    expect(screen.getByLabelText(/Open emergency protocols/)).toBeInTheDocument()
  })

  it('toggles satellite layer from menu', function() {
    render(React.createElement(FloatingSidebarControls))
    fireEvent.click(screen.getByLabelText(/Map Layers/))
    fireEvent.click(screen.getByLabelText('Toggle Satellite layer'))
    expect(mockStore.setShowSatellite).toHaveBeenCalledWith(true)
  })

  it('does not show heatmap legend when heatmap off', function() {
    render(React.createElement(FloatingSidebarControls))
    fireEvent.click(screen.getByLabelText(/Map Layers/))
    expect(screen.queryByText('Hazard Legend')).not.toBeInTheDocument()
  })

  it('shows heatmap legend when heatmap active', function() {
    mockStore.showHazardHeatmap = true
    render(React.createElement(FloatingSidebarControls))
    fireEvent.click(screen.getByLabelText(/Map Layers/))
    expect(screen.getByText('Hazard Legend')).toBeInTheDocument()
    expect(screen.getByText('High Severity (S4+)')).toBeInTheDocument()
    mockStore.showHazardHeatmap = false
  })

  it('toggles satellite layer off', function() {
    mockStore.showSatellite = true
    render(React.createElement(FloatingSidebarControls))
    fireEvent.click(screen.getByLabelText(/Map Layers/))
    fireEvent.click(screen.getByLabelText('Toggle Satellite layer'))
    expect(mockStore.setShowSatellite).toHaveBeenCalledWith(false)
    mockStore.showSatellite = false
  })

  it('toggles hazard heatmap on', function() {
    render(React.createElement(FloatingSidebarControls))
    fireEvent.click(screen.getByLabelText(/Map Layers/))
    fireEvent.click(screen.getByLabelText('Toggle Hazard Heatmap layer'))
    expect(mockStore.setShowHazardHeatmap).toHaveBeenCalledWith(true)
  })

  it('shows weather & flood in heatmap legend', function() {
    mockStore.showHazardHeatmap = true
    render(React.createElement(FloatingSidebarControls))
    fireEvent.click(screen.getByLabelText(/Map Layers/))
    expect(screen.getByText('Weather & Flood')).toBeInTheDocument()
    mockStore.showHazardHeatmap = false
  })

  it('dispatches custom event on relocate click', function() {
    const dispatchSpy = jest.fn()
    window.dispatchEvent = dispatchSpy
    jest.useFakeTimers()
    render(React.createElement(FloatingSidebarControls))
    fireEvent.click(screen.getByLabelText(/Re-center map/))
    expect(dispatchSpy).toHaveBeenCalledWith(expect.objectContaining({ type: 'svai:refresh-location' }))
    jest.advanceTimersByTime(2000)
    jest.useRealTimers()
  })

  it('shows emergency protocols link', function() {
    render(React.createElement(FloatingSidebarControls))
    const emergencyBtn = screen.getByLabelText(/Open emergency protocols/)
    expect(emergencyBtn.closest('a')).toHaveAttribute('href', '/emergency')
  })

  it('renders SOS button with correct styling', function() {
    render(React.createElement(FloatingSidebarControls))
    const sosBtn = screen.getByText('SOS').closest('button')
    expect(sosBtn).toBeInTheDocument()
    expect(sosBtn?.className).toContain('sos-rings')
  })

  it('shows CRITICAL label when driving score below 60', function() {
    mockStore.drivingScore = 50
    render(React.createElement(FloatingSidebarControls))
    expect(screen.getByText('CRITICAL')).toBeInTheDocument()
    mockStore.drivingScore = 78
  })

  it('shows CAUTION label when driving score between 60 and 79', function() {
    mockStore.drivingScore = 70
    render(React.createElement(FloatingSidebarControls))
    expect(screen.getByText('CAUTION')).toBeInTheDocument()
    mockStore.drivingScore = 78
  })

  it('toggles traffic layer from menu', function() {
    render(React.createElement(FloatingSidebarControls))
    fireEvent.click(screen.getByLabelText(/Map Layers/))
    fireEvent.click(screen.getByLabelText('Toggle Traffic layer'))
    expect(mockStore.setShowTraffic).toHaveBeenCalledWith(true)
  })

  it('toggles emergency services layer from menu', function() {
    render(React.createElement(FloatingSidebarControls))
    fireEvent.click(screen.getByLabelText(/Map Layers/))
    fireEvent.click(screen.getByLabelText('Toggle Emergency Services layer'))
    expect(mockStore.setShowEmergencyServices).toHaveBeenCalledWith(false)
  })

  it('navigates to SOS page on emergency button click', function() {
    render(React.createElement(FloatingSidebarControls))
    const sosBtn = screen.getByText('SOS').closest('button')
    fireEvent.click(sosBtn!)
    expect(mockPush).toHaveBeenCalledWith('/sos')
  })

  it('shows scanning overlay after relocate click', function() {
    jest.useFakeTimers()
    const dispatchSpy = jest.fn()
    window.dispatchEvent = dispatchSpy
    render(React.createElement(FloatingSidebarControls))
    fireEvent.click(screen.getByLabelText(/Re-center map/))
    jest.advanceTimersByTime(50)
    const sosBtn = screen.getByText('SOS').closest('button')
    expect(sosBtn?.innerHTML).toContain('blur-xl')
    jest.advanceTimersByTime(2000)
    jest.useRealTimers()
  })
})
