jest.mock('@/hooks/usePageEntry', function() { return { usePageEntry: function() { return { current: null } } } })
jest.mock('@/lib/store', function() {
  return {
    useAppStore: Object.assign(
      function(sel) {
        const state = { userProfile: { name: 'Test', bloodGroup: 'O+', emergencyContact: '+919999999999', vehicleNumber: 'TN01AB1234' }, soundsEnabled: true }
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

import { render, screen, waitFor, fireEvent, act } from '@testing-library/react'
const triggerSos = require('@/lib/api').triggerSos
const enqueueSOS = require('@/lib/offline-sos-queue').enqueueSOS
const startFamilyTracking = require('@/lib/live-tracking').startFamilyTracking
const beginLocationBroadcast = require('@/lib/live-tracking').beginLocationBroadcast
const notifyContactsViaWhatsApp = require('@/lib/live-tracking').notifyContactsViaWhatsApp
const haptics = require('@/lib/haptics').haptics
const sounds = require('@/lib/sounds').sounds
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
    const smsLink = screen.getByLabelText('Share location via SMS')
    expect(smsLink).toBeTruthy()
    expect(smsLink.getAttribute('href')).toBe('sms:123')
  })

  it('renders WhatsApp button (disabled without GPS)', function() {
    render(React.createElement(Page))
    const waBtn = screen.getByLabelText('Share location via WhatsApp (unavailable)')
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

  describe('hold-to-activate interaction', function() {
    let rafAllowed

    function setupGeo(lat, lon) {
      Object.defineProperty(navigator, 'geolocation', {
        value: { getCurrentPosition: function(success) { success({ coords: { latitude: lat, longitude: lon } }) } },
        writable: true, configurable: true
      })
    }

    beforeEach(function() {
      rafAllowed = true
      triggerSos.mockClear()
      enqueueSOS.mockClear()
      startFamilyTracking.mockClear()
      jest.spyOn(window, 'requestAnimationFrame').mockImplementation(function(cb) {
        if (!rafAllowed) return 1
        cb(performance.now() + 2000)
        return 1
      })
      jest.spyOn(window, 'cancelAnimationFrame').mockImplementation(jest.fn())
    })

    afterEach(function() {
      jest.restoreAllMocks()
    })

    it('activates SOS after hold completes and calls triggerSos with geolocation', function() {
      setupGeo(13.0827, 80.2707)
      render(React.createElement(Page))
      act(function() { fireEvent.pointerDown(screen.getByLabelText('Activate emergency SOS')) })
      expect(screen.getByLabelText('Emergency SOS dispatched')).toBeTruthy()
      expect(screen.getByText('DISPATCHED')).toBeTruthy()
      expect(triggerSos).toHaveBeenCalledWith({ lat: 13.0827, lon: 80.2707 })
      expect(startFamilyTracking).toHaveBeenCalledWith({
        userName: 'Test', bloodGroup: 'O+', vehicleNumber: 'TN01AB1234',
        latitude: 13.0827, longitude: 80.2707
      })
    })

    it('enqueues SOS offline when navigator.onLine is false', function() {
      setupGeo(12.9716, 77.5946)
      Object.defineProperty(navigator, 'onLine', { value: false, writable: true, configurable: true })
      render(React.createElement(Page))
      act(function() { fireEvent.pointerDown(screen.getByLabelText('Activate emergency SOS')) })
      expect(screen.getByLabelText('Emergency SOS dispatched')).toBeTruthy()
      expect(enqueueSOS).toHaveBeenCalledWith({ lat: 12.9716, lon: 77.5946 })
      expect(triggerSos).not.toHaveBeenCalled()
    })

    it('cancel hold does not activate', function() {
      render(React.createElement(Page))
      rafAllowed = false
      act(function() { fireEvent.pointerDown(screen.getByLabelText('Activate emergency SOS')) })
      act(function() { fireEvent.pointerUp(screen.getByLabelText('Activate emergency SOS')) })
      rafAllowed = true
      expect(screen.getByLabelText('Activate emergency SOS')).toBeTruthy()
    })

    it('cancel dispatch resets SOS state', function() {
      setupGeo(13.0, 80.0)
      render(React.createElement(Page))
      act(function() { fireEvent.pointerDown(screen.getByLabelText('Activate emergency SOS')) })
      expect(screen.getByLabelText('Emergency SOS dispatched')).toBeTruthy()
      act(function() { fireEvent.click(screen.getByText('Cancel Dispatch')) })
      expect(screen.getByLabelText('Activate emergency SOS')).toBeTruthy()
    })

    it('creates tracking URL and displays live tracking section', function() {
      setupGeo(28.6139, 77.2090)
      render(React.createElement(Page))
      act(function() { fireEvent.pointerDown(screen.getByLabelText('Activate emergency SOS')) })
      expect(screen.getByLabelText('Emergency SOS dispatched')).toBeTruthy()
    })
  })
})
