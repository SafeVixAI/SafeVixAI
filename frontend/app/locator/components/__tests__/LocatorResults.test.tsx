jest.mock('@gsap/react', function() { return { useGSAP: jest.fn() } })
jest.mock('@/lib/gsap', function() { return { gsap: { fromTo: jest.fn(), to: jest.fn() } } })
jest.mock('@tanstack/react-virtual', function() {
  return {
    useVirtualizer: jest.fn(function() {
      return {
        getVirtualItems: function() {
          return [
            { key: 0, index: 0, start: 0, size: 190 },
            { key: 1, index: 1, start: 190, size: 190 },
          ]
        },
        getTotalSize: function() { return 380 },
      }
    }),
  }
})

import { render, screen, fireEvent } from '@testing-library/react'
import React from 'react'
import { MobileResultsList, DesktopResultsList } from '../LocatorResults'

var mockServices = [
  { id: 's1', name: 'City Hospital', type: 'Hospital', filterType: 'Hospital' as const, distance: '500 m', address: 'Main Rd', accentColor: '#ef4444', coords: [13, 80] as [number, number], phone: '1234567890', category: 'hospital' as const },
  { id: 's2', name: 'Police Station', type: 'Police', filterType: 'Police' as const, distance: '1.2 km', address: 'Market St', accentColor: '#3b82f6', coords: [13.1, 80.1] as [number, number], phone: '100', category: 'police' as const },
]

var defaultProps = {
  filtered: mockServices,
  selectedServiceId: null,
  routeLoadingId: null,
  onLocateService: jest.fn(),
  onPreviewService: jest.fn(),
}

describe('MobileResultsList', function() {
  beforeEach(function() { jest.clearAllMocks() })

  it('renders service cards', function() {
    render(React.createElement(MobileResultsList, defaultProps))
    expect(screen.getByText('City Hospital')).toBeInTheDocument()
    expect(screen.getByText('Police Station')).toBeInTheDocument()
  })

  it('renders distance badges', function() {
    render(React.createElement(MobileResultsList, defaultProps))
    expect(screen.getByText('500 m')).toBeInTheDocument()
    expect(screen.getByText('1.2 km')).toBeInTheDocument()
  })

  it('renders addresses', function() {
    render(React.createElement(MobileResultsList, defaultProps))
    expect(screen.getByText('Main Rd')).toBeInTheDocument()
    expect(screen.getByText('Market St')).toBeInTheDocument()
  })

  it('renders Call buttons with phone links', function() {
    render(React.createElement(MobileResultsList, defaultProps))
    var calls = screen.getAllByText('Call')
    expect(calls).toHaveLength(2)
  })

  it('renders Locate buttons', function() {
    render(React.createElement(MobileResultsList, defaultProps))
    var locates = screen.getAllByText('Locate')
    expect(locates).toHaveLength(2)
  })

  it('renders Focus buttons', function() {
    render(React.createElement(MobileResultsList, defaultProps))
    var focuses = screen.getAllByText('Focus')
    expect(focuses).toHaveLength(2)
  })

  it('calls onLocateService when Locate clicked', function() {
    var onLocate = jest.fn()
    render(React.createElement(MobileResultsList, { ...defaultProps, onLocateService: onLocate }))
    fireEvent.click(screen.getAllByText('Locate')[0])
    expect(onLocate).toHaveBeenCalledWith(mockServices[0])
  })

  it('calls onPreviewService when Focus clicked', function() {
    var onPreview = jest.fn()
    render(React.createElement(MobileResultsList, { ...defaultProps, onPreviewService: onPreview }))
    fireEvent.click(screen.getAllByText('Focus')[1])
    expect(onPreview).toHaveBeenCalledWith(mockServices[1])
  })

  it('disables Locate button when routeLoadingId matches', function() {
    render(React.createElement(MobileResultsList, { ...defaultProps, routeLoadingId: 's1' }))
    // s1 shows "Routing" instead of "Locate", so only 1 Locate button (for s2)
    expect(screen.getAllByText('Locate')).toHaveLength(1)
  })

  it('shows Routing text when loading', function() {
    render(React.createElement(MobileResultsList, { ...defaultProps, routeLoadingId: 's1' }))
    expect(screen.getByText('Routing')).toBeInTheDocument()
  })

  it('applies selected style when selectedServiceId matches', function() {
    var { container } = render(React.createElement(MobileResultsList, { ...defaultProps, selectedServiceId: 's1' }))
    var cards = container.querySelectorAll('.locator-result-card')
    expect(cards[0].className).toContain('border-brand/30')
  })
})

describe('DesktopResultsList', function() {
  beforeEach(function() { jest.clearAllMocks() })

  it('renders service cards', function() {
    render(React.createElement(DesktopResultsList, defaultProps))
    expect(screen.getByText('City Hospital')).toBeInTheDocument()
    expect(screen.getByText('Police Station')).toBeInTheDocument()
  })

  it('renders distance badges', function() {
    render(React.createElement(DesktopResultsList, defaultProps))
    expect(screen.getByText('500 m')).toBeInTheDocument()
    expect(screen.getByText('1.2 km')).toBeInTheDocument()
  })

  it('renders addresses', function() {
    render(React.createElement(DesktopResultsList, defaultProps))
    expect(screen.getByText('Main Rd')).toBeInTheDocument()
  })

  it('renders Call buttons', function() {
    render(React.createElement(DesktopResultsList, defaultProps))
    var calls = screen.getAllByText('Call')
    expect(calls).toHaveLength(2)
  })

  it('renders Locate buttons', function() {
    render(React.createElement(DesktopResultsList, defaultProps))
    expect(screen.getAllByText('Locate')).toHaveLength(2)
  })

  it('calls onLocateService when Locate clicked', function() {
    var onLocate = jest.fn()
    render(React.createElement(DesktopResultsList, { ...defaultProps, onLocateService: onLocate }))
    fireEvent.click(screen.getAllByText('Locate')[0])
    expect(onLocate).toHaveBeenCalledWith(mockServices[0])
  })

  it('calls onPreviewService when Focus clicked', function() {
    var onPreview = jest.fn()
    render(React.createElement(DesktopResultsList, { ...defaultProps, onPreviewService: onPreview }))
    fireEvent.click(screen.getAllByText('Focus')[1])
    expect(onPreview).toHaveBeenCalledWith(mockServices[1])
  })

  it('shows Routing spinner when loading', function() {
    render(React.createElement(DesktopResultsList, { ...defaultProps, routeLoadingId: 's1' }))
    expect(screen.getByText('Routing')).toBeInTheDocument()
    expect(screen.getByText('Locate')).toBeInTheDocument()
  })

  it('applies selected style when selectedServiceId matches', function() {
    var { container } = render(React.createElement(DesktopResultsList, { ...defaultProps, selectedServiceId: 's2' }))
    var cards = container.querySelectorAll('.locator-result-card')
    expect(cards[1].className).toContain('border-brand/30')
  })
})
