import React from 'react'

var mockPosthogInit = jest.fn()
var mockPosthog = { init: mockPosthogInit, capture: jest.fn() }
var mockPostHogProvider = function MockPostHogProvider(_a: any) { var children = _a.children; return React.createElement(React.Fragment, null, children) }

jest.mock('posthog-js', function() { return { __esModule: true, default: mockPosthog } })
jest.mock('posthog-js/react', function() { return { __esModule: true, PostHogProvider: mockPostHogProvider } })

import { render, screen } from '@testing-library/react'
import { AnalyticsProvider } from '../analytics-provider'
import { useAppStore } from '../store'

var originalEnv = process.env

beforeEach(function() {
  process.env = { ...originalEnv }
  localStorage.clear()
  mockPosthogInit.mockClear()
})

afterEach(function() {
  process.env = originalEnv
})

describe('AnalyticsProvider', function() {
  beforeEach(function() {
    useAppStore.setState({ analyticsOptIn: false })
  })

  it('renders children', function() {
    render(React.createElement(AnalyticsProvider, null, React.createElement('div', { 'data-testid': 'child' }, 'Hello')))
    expect(screen.getByTestId('child')).toBeInTheDocument()
  })

  it('renders children without PostHog when no key', function() {
    render(React.createElement(AnalyticsProvider, null, React.createElement('div', { 'data-testid': 'child' }, 'Hello')))
    expect(screen.getByTestId('child')).toBeInTheDocument()
    expect(mockPosthogInit).not.toHaveBeenCalled()
  })

  it('renders children when PostHog key present and consent granted', function() {
    process.env.NEXT_PUBLIC_POSTHOG_KEY = 'test-key'
    localStorage.setItem('safevixai:analytics-consent', 'granted')
    render(React.createElement(AnalyticsProvider, null, React.createElement('div', { 'data-testid': 'child' }, 'Hello')))
    expect(screen.getByTestId('child')).toBeInTheDocument()
  })

  it('handles analyticsOptIn from store with key present', function() {
    process.env.NEXT_PUBLIC_POSTHOG_KEY = 'phc_test'
    localStorage.removeItem('safevixai:analytics-consent')
    render(React.createElement(AnalyticsProvider, null, React.createElement('div', { 'data-testid': 'child' }, 'Hello')))
    expect(screen.getByTestId('child')).toBeInTheDocument()
  })

  it('renders children when opted in but no PostHog key', function() {
    delete process.env.NEXT_PUBLIC_POSTHOG_KEY
    useAppStore.setState({ analyticsOptIn: true })
    render(React.createElement(AnalyticsProvider, null, React.createElement('div', { 'data-testid': 'child' }, 'Hello')))
    expect(screen.getByTestId('child')).toBeInTheDocument()
    expect(mockPosthogInit).not.toHaveBeenCalled()
  })
})
