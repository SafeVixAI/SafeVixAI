// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
jest.mock('@/lib/api', function() {
  return { fetchCsrfToken: jest.fn().mockResolvedValue(undefined) }
})

jest.mock('@/lib/public-env', function() {
  return { PUBLIC_API_BASE_URL: 'http://localhost:8000', PUBLIC_CHATBOT_BASE_URL: 'http://localhost:8010' }
})

import { render, waitFor, act } from '@testing-library/react'
import React from 'react'

beforeEach(function() {
  jest.useFakeTimers()
  global.fetch = jest.fn().mockResolvedValue({ ok: true })
})

afterEach(function() {
  jest.useRealTimers()
})

function TestCase() {
  require('../useKeepAlivePing').useKeepAlivePing()
  return React.createElement('div')
}

describe('useKeepAlivePing', function() {
  it('pings endpoints on mount', async function() {
    render(React.createElement(TestCase))
    await act(async function() {})
    expect(global.fetch).toHaveBeenCalled()
  })

  it('pings again when visibility changes to visible', async function() {
    render(React.createElement(TestCase))
    await act(async function() {})
    const callCount = (global.fetch as jest.Mock).mock.calls.length
    Object.defineProperty(document, 'visibilityState', { value: 'visible', configurable: true })
    document.dispatchEvent(new Event('visibilitychange'))
    expect((global.fetch as jest.Mock).mock.calls.length).toBeGreaterThan(callCount)
  })

  it('does not ping when visibility changes to hidden', async function() {
    render(React.createElement(TestCase))
    await act(async function() {})
    const callCount = (global.fetch as jest.Mock).mock.calls.length
    Object.defineProperty(document, 'visibilityState', { value: 'hidden', configurable: true })
    document.dispatchEvent(new Event('visibilitychange'))
    expect((global.fetch as jest.Mock).mock.calls.length).toBe(callCount)
  })

  it('cleans up on unmount', async function() {
    const comp = render(React.createElement(TestCase))
    await act(async function() {})
    const clearIntervalSpy = jest.spyOn(globalThis, 'clearInterval')
    comp.unmount()
    expect(clearIntervalSpy).toHaveBeenCalled()
    clearIntervalSpy.mockRestore()
  })
})
