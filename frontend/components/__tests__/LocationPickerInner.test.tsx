// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
import { render, screen, fireEvent, act, waitFor } from '@testing-library/react'
import React from 'react'

var markerCallbacks: Record<string, Function> = {}
jest.mock('maplibre-gl', function () {
  var mockMarker = {
    setLngLat: jest.fn().mockImplementation(function () { return mockMarker }),
    addTo: jest.fn().mockImplementation(function () { return mockMarker }),
    on: jest.fn().mockImplementation(function (event, cb) {
      markerCallbacks[event] = cb
      return mockMarker
    }),
    getLngLat: jest.fn().mockReturnValue({ lat: 13, lng: 80 }),
    remove: jest.fn(),
  }
  return {
    Map: jest.fn(function () { return {
      addControl: jest.fn(),
      remove: jest.fn(),
      flyTo: jest.fn(),
      on: jest.fn(),
    } }),
    Marker: jest.fn(function () { return mockMarker }),
    NavigationControl: jest.fn(),
  }
})

jest.mock('react-i18next', function () { return { useTranslation: function () { return { t: function (k: string, fallback?: string) { return typeof fallback === 'string' ? fallback : k } } } } })

var mockFetch = jest.fn()
global.fetch = mockFetch

describe('LocationPickerInner', function () {
  beforeEach(function () {
    mockFetch.mockReset()
    mockFetch.mockResolvedValue({ ok: true, json: async function () { return { locality: 'Chennai', city: 'Chennai', principalSubdivision: 'Tamil Nadu' } } })
  })

  it('renders map container and address display', async function () {
    var LocationPickerInner = (await import('../report/LocationPickerInner')).default
    var onLocationChange = jest.fn()
    render(React.createElement(LocationPickerInner, { lat: 13, lon: 80, onLocationChange: onLocationChange, className: 'test-class' }))
    expect(screen.getByText('Drag the pin to adjust location')).toBeInTheDocument()
  })

  it('renders with zero coordinates and shows detecting', async function () {
    var LocationPickerInner = (await import('../report/LocationPickerInner')).default
    var onLocationChange = jest.fn()
    render(React.createElement(LocationPickerInner, { lat: 0, lon: 0, onLocationChange: onLocationChange }))
    expect(screen.getByText('Detecting location...')).toBeInTheDocument()
    expect(screen.getByText('Drag the pin to adjust location')).toBeInTheDocument()
  })

  it('displays geocoded address with non-zero coords', async function () {
    var LocationPickerInner = (await import('../report/LocationPickerInner')).default
    var onLocationChange = jest.fn()
    render(React.createElement(LocationPickerInner, { lat: 13, lon: 80, onLocationChange: onLocationChange }))
    await screen.findByText('Chennai, Chennai, Tamil Nadu')
  })

  it('handles geocode fetch error with fallback coords', async function () {
    jest.useFakeTimers()
    mockFetch.mockRejectedValue(new Error('Network error'))
    var LocationPickerInner = (await import('../report/LocationPickerInner')).default
    var onLocationChange = jest.fn()
    render(React.createElement(LocationPickerInner, { lat: 13, lon: 80, onLocationChange: onLocationChange }))
    await act(async function() { jest.runAllTimers() })
    await waitFor(function() { expect(onLocationChange).toHaveBeenCalled() }, { timeout: 5000 })
    jest.useRealTimers()
  })

  it('renders recenter button', async function () {
    var LocationPickerInner = (await import('../report/LocationPickerInner')).default
    var onLocationChange = jest.fn()
    render(React.createElement(LocationPickerInner, { lat: 13, lon: 80, onLocationChange: onLocationChange }))
    expect(screen.getByLabelText(/Recenter map/)).toBeInTheDocument()
  })

  it('calls reverseGeocode on marker drag end', async function () {
    jest.useFakeTimers()
    mockFetch.mockResolvedValue({ ok: true, json: async function () { return { locality: 'Guindy', city: 'Chennai', principalSubdivision: 'Tamil Nadu' } } })
    var LocationPickerInner = (await import('../report/LocationPickerInner')).default
    var onLocationChange = jest.fn()
    render(React.createElement(LocationPickerInner, { lat: 13, lon: 80, onLocationChange: onLocationChange }))
    await screen.findByText('Drag the pin to adjust location')
    act(function () { markerCallbacks['dragend']() })
    await act(async function () { jest.runAllTimers() })
    await waitFor(function () { expect(onLocationChange).toHaveBeenCalled() }, { timeout: 5000 })
    jest.useRealTimers()
  })

  it('recenters on user location via geolocation', async function () {
    var getCurrentPosition = jest.fn(function (success) {
      success({ coords: { latitude: 13.1, longitude: 80.1 } })
    })
    Object.defineProperty(navigator, 'geolocation', {
      value: { getCurrentPosition },
      configurable: true,
    })
    var LocationPickerInner = (await import('../report/LocationPickerInner')).default
    var onLocationChange = jest.fn()
    render(React.createElement(LocationPickerInner, { lat: 13, lon: 80, onLocationChange: onLocationChange }))
    fireEvent.click(screen.getByLabelText(/Recenter map/))
    await waitFor(function () { expect(onLocationChange).toHaveBeenCalled() })
    var calls = onLocationChange.mock.calls
    var lastCall = calls[calls.length - 1]
    expect(lastCall[0]).toBe(13.1)
    expect(lastCall[1]).toBe(80.1)
  })
})
