// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

var mockSetLocationTracking = jest.fn()
jest.mock('@/lib/store', function() {
  return {
    useAppStore: function(selector: any) {
      return selector({ setLocationTracking: mockSetLocationTracking })
    },
  }
})

import { render, screen, fireEvent, act } from '@testing-library/react'
import React from 'react'
import GpsConsent, { GPS_CONSENT_KEY } from '../ui/GpsConsent'

describe('GpsConsent', function() {
  beforeEach(function() {
    jest.clearAllMocks()
    localStorage.clear()
    jest.useFakeTimers()
  })

  afterEach(function() {
    jest.useRealTimers()
  })

  it('starts hidden', function() {
    var { container } = render(React.createElement(GpsConsent))
    expect(container.innerHTML).toBe('')
  })

  it('appears after 3500ms when no prior consent', function() {
    render(React.createElement(GpsConsent))
    act(function() { jest.advanceTimersByTime(3500) })
    expect(screen.getByText('Location Privacy')).toBeTruthy()
    expect(screen.getByText('Authorize')).toBeTruthy()
    expect(screen.getByText('Restrict')).toBeTruthy()
  })

  it('stays hidden when consent already stored', function() {
    localStorage.setItem(GPS_CONSENT_KEY, 'granted')
    var { container } = render(React.createElement(GpsConsent))
    act(function() { jest.advanceTimersByTime(5000) })
    expect(container.innerHTML).toBe('')
  })

  it('calls setLocationTracking(true) and stores consent on Authorize', function() {
    render(React.createElement(GpsConsent))
    act(function() { jest.advanceTimersByTime(3500) })
    fireEvent.click(screen.getByText('Authorize'))
    expect(mockSetLocationTracking).toHaveBeenCalledWith(true)
    expect(localStorage.getItem(GPS_CONSENT_KEY)).toBe('granted')
  })

  it('calls setLocationTracking(false) and stores denial on Restrict', function() {
    render(React.createElement(GpsConsent))
    act(function() { jest.advanceTimersByTime(3500) })
    fireEvent.click(screen.getByText('Restrict'))
    expect(mockSetLocationTracking).toHaveBeenCalledWith(false)
    expect(localStorage.getItem(GPS_CONSENT_KEY)).toBe('denied')
  })

  it('calls setLocationTracking(false) and stores denial on X dismiss', function() {
    render(React.createElement(GpsConsent))
    act(function() { jest.advanceTimersByTime(3500) })
    fireEvent.click(screen.getByLabelText('Dismiss location banner'))
    expect(mockSetLocationTracking).toHaveBeenCalledWith(false)
    expect(localStorage.getItem(GPS_CONSENT_KEY)).toBe('denied')
  })

  it('skips rendering when E2E bypass flag is set', function() {
    localStorage.setItem('__E2E_SKIP_AUTH__', 'true')
    var { container } = render(React.createElement(GpsConsent))
    act(function() { jest.advanceTimersByTime(5000) })
    expect(container.innerHTML).toBe('')
  })
})
