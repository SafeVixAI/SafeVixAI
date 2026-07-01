jest.mock('@/hooks/usePageEntry', function() { return { usePageEntry: function() { return { current: null } } } })
jest.mock('@/lib/store', function() {
  return {
    useAppStore: Object.assign(
      function(sel) {
        var state = { userProfile: { name: 'Test', bloodGroup: 'O+', emergencyContact: '+919999999999', vehicleNumber: 'TN01AB1234' }, soundsEnabled: true }
        return typeof sel === 'function' ? sel(state) : state
      },
      { getState: function() { return {} }, setState: jest.fn(), subscribe: jest.fn() }
    )
  }
})
jest.mock('next/navigation', function() { return { useRouter: function() { return { push: jest.fn(), back: jest.fn() } }, useSearchParams: function() { return new URLSearchParams() } } })
jest.mock('next/image', function() { return function() { return null } })
jest.mock('zustand/react/shallow', function() { return { useShallow: function(fn) { return fn } } })
jest.mock('@/lib/api', function() { return { triggerSos: jest.fn().mockResolvedValue({}) } })
jest.mock('@/lib/offline-sos-queue', function() { return { enqueueSOS: jest.fn().mockResolvedValue(undefined) } })
jest.mock('@/lib/sos-share', function() { return { generateSosWhatsAppLink: jest.fn().mockResolvedValue('https://wa.me/123'), generateSosSmsLink: jest.fn().mockReturnValue('sms:123') } })
jest.mock('@/lib/live-tracking', function() { return { startFamilyTracking: jest.fn().mockResolvedValue({ tracking_url: 'https://track.safevixai.app/abc', session_id: 'sess-1' }), beginLocationBroadcast: jest.fn().mockReturnValue(function() {}), notifyContactsViaWhatsApp: jest.fn() } })
jest.mock('@/components/dashboard/TopSearch', function() { return function() { return null } })
jest.mock('@/components/dashboard/SystemHeader', function() { return function() { return null } })
jest.mock('@/lib/haptics', function() { return { haptics: { medium: jest.fn(), sos: jest.fn() } } })
jest.mock('@/lib/sounds', function() { return { sounds: { sosSent: jest.fn() } } })
jest.mock('@/lib/analytics', function() { return { track: { trackingShared: jest.fn() } } })
jest.mock('lucide-react', function() { return new Proxy({}, { get: function() { return function() { return null } } }) })

import { render, screen, waitFor } from '@testing-library/react'
import React from 'react'
import Page from '../app/sos/page'

describe('SOSPage', function() {
  it('renders Hold to Activate text', function() {
    render(React.createElement(Page))
    expect(screen.getByText('Hold to Activate')).toBeTruthy()
  })

  it('renders emergency contact numbers', function() {
    render(React.createElement(Page))
    expect(screen.getByText('112')).toBeTruthy()
    expect(screen.getByText('100')).toBeTruthy()
    expect(screen.getByText('102')).toBeTruthy()
  })

  it('renders emergency service labels', function() {
    render(React.createElement(Page))
    expect(screen.getByText('Emergency')).toBeTruthy()
    expect(screen.getByText('Police')).toBeTruthy()
    expect(screen.getByText('Ambulance')).toBeTruthy()
  })

  it('renders crash profile section with labels', function() {
    render(React.createElement(Page))
    expect(screen.getByText('Blood Group')).toBeTruthy()
    expect(screen.getByText('Primary Contact')).toBeTruthy()
    expect(screen.getByText('Operator')).toBeTruthy()
  })

  it('renders Share Location and Crash Profile section headings', function() {
    render(React.createElement(Page))
    expect(screen.getByText('Share Location')).toBeTruthy()
    expect(screen.getByText('Crash Profile')).toBeTruthy()
    expect(screen.getByText('Vehicle ID')).toBeTruthy()
  })

  it('renders G-Force impact badge with default value', function() {
    render(React.createElement(Page))
    expect(screen.getByText('1.0G IMPACT')).toBeTruthy()
  })

  it('renders SOS button with correct aria-label', function() {
    render(React.createElement(Page))
    expect(screen.getByLabelText('Activate emergency SOS')).toBeTruthy()
  })

  it('shows geolocation error in JSDOM (no GPS)', function() {
    render(React.createElement(Page))
    expect(screen.getByText('Geolocation not supported by this browser.')).toBeTruthy()
  })

  it('renders SMS Backup link with correct href', function() {
    render(React.createElement(Page))
    var smsLink = screen.getByLabelText('Share location via SMS')
    expect(smsLink).toBeTruthy()
    expect(smsLink.getAttribute('href')).toBe('sms:123')
  })

  it('renders WhatsApp button (disabled without GPS)', function() {
    render(React.createElement(Page))
    var waBtn = screen.getByLabelText('Share location via WhatsApp (unavailable)')
    expect(waBtn).toBeTruthy()
  })

  it('renders Automatic Emergency Dispatch armed text', function() {
    render(React.createElement(Page))
    expect(screen.getByText('Automatic Emergency Dispatch system armed')).toBeTruthy()
  })

  it('renders crash profile blood group value', function() {
    render(React.createElement(Page))
    expect(screen.getByText('O+')).toBeTruthy()
  })

  it('renders crash profile vehicle number', function() {
    render(React.createElement(Page))
    expect(screen.getByText('TN01AB1234')).toBeTruthy()
  })

  it('renders Real-time Fix badge', function() {
    render(React.createElement(Page))
    expect(screen.getByText('Real-time Fix')).toBeTruthy()
  })

  it('renders GPS Coordinates Preview label', function() {
    render(React.createElement(Page))
    expect(screen.getByText('GPS Coordinates Preview')).toBeTruthy()
  })
})
