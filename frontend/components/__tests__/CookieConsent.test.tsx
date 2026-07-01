// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

var mockSetAnalyticsOptIn = jest.fn()
jest.mock('@/lib/store', function() {
  return {
    useAppStore: function(selector: any) {
      return selector({ setAnalyticsOptIn: mockSetAnalyticsOptIn })
    },
  }
})

jest.mock('@/lib/analytics-provider', function() {
  return { ANALYTICS_CONSENT_KEY: 'safevixai:analytics-consent' }
})

import { render, screen, fireEvent, act } from '@testing-library/react'
import React from 'react'
import posthog from 'posthog-js'
import CookieConsent from '../ui/CookieConsent'
import { ANALYTICS_CONSENT_KEY } from '@/lib/analytics-provider'

describe('CookieConsent', function() {
  beforeEach(function() {
    jest.clearAllMocks()
    localStorage.clear()
    jest.useFakeTimers()
  })

  afterEach(function() {
    jest.useRealTimers()
  })

  it('starts hidden', function() {
    var { container } = render(React.createElement(CookieConsent))
    expect(container.innerHTML).toBe('')
  })

  it('appears after 2000ms when no prior consent', function() {
    render(React.createElement(CookieConsent))
    act(function() { jest.advanceTimersByTime(2000) })
    expect(screen.getByText('Privacy & Consent')).toBeTruthy()
    expect(screen.getByText('Accept')).toBeTruthy()
    expect(screen.getByText('Decline')).toBeTruthy()
  })

  it('stays hidden when consent already stored', function() {
    localStorage.setItem(ANALYTICS_CONSENT_KEY, 'granted')
    var { container } = render(React.createElement(CookieConsent))
    act(function() { jest.advanceTimersByTime(5000) })
    expect(container.innerHTML).toBe('')
  })

  it('calls posthog.opt_in_capturing on Accept', function() {
    render(React.createElement(CookieConsent))
    act(function() { jest.advanceTimersByTime(2000) })
    fireEvent.click(screen.getByText('Accept'))
    expect(posthog.opt_in_capturing).toHaveBeenCalled()
    expect(mockSetAnalyticsOptIn).toHaveBeenCalledWith(true)
    expect(localStorage.getItem(ANALYTICS_CONSENT_KEY)).toBe('granted')
  })

  it('calls posthog.opt_out_capturing on Decline', function() {
    render(React.createElement(CookieConsent))
    act(function() { jest.advanceTimersByTime(2000) })
    fireEvent.click(screen.getByText('Decline'))
    expect(posthog.opt_out_capturing).toHaveBeenCalled()
    expect(mockSetAnalyticsOptIn).toHaveBeenCalledWith(false)
    expect(localStorage.getItem(ANALYTICS_CONSENT_KEY)).toBe('denied')
  })

  it('stays hidden when E2E skip flag is set', function() {
    localStorage.setItem('__E2E_SKIP_AUTH__', 'true')
    var { container } = render(React.createElement(CookieConsent))
    act(function() { jest.advanceTimersByTime(5000) })
    expect(container.innerHTML).toBe('')
  })

  it('has a link to privacy policy', function() {
    render(React.createElement(CookieConsent))
    act(function() { jest.advanceTimersByTime(2000) })
    expect(screen.getByText('View Policy')).toBeTruthy()
  })

  it('dismisses banner via X button', function() {
    render(React.createElement(CookieConsent))
    act(function() { jest.advanceTimersByTime(2000) })
    fireEvent.click(screen.getByLabelText('Dismiss banner'))
    expect(posthog.opt_out_capturing).toHaveBeenCalled()
    expect(mockSetAnalyticsOptIn).toHaveBeenCalledWith(false)
    expect(localStorage.getItem(ANALYTICS_CONSENT_KEY)).toBe('denied')
  })
})
