// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
jest.mock('@/lib/crash-detection', function() {
  return {
    startCrashDetection: jest.fn(),
    stopCrashDetection: jest.fn(),
    simulateCrashDemo: jest.fn().mockReturnValue('simulated'),
  }
})

import { render } from '@testing-library/react'
import React from 'react'

beforeEach(function() {
  jest.clearAllMocks()
})

function TestCase({ onCrash, enabled }: { onCrash?: (f: number) => void; enabled?: boolean }) {
  const hook = require('../useCrashDetection').useCrashDetection
  const result = hook({ onCrashDetected: onCrash || jest.fn(), enabled: enabled })
  return React.createElement('div', { 'data-simulate': typeof result.simulateCrash })
}

describe('useCrashDetection', function() {
  it('starts crash detection when enabled', function() {
    const crash = require('@/lib/crash-detection')
    render(React.createElement(TestCase, { enabled: true }))
    expect(crash.startCrashDetection).toHaveBeenCalled()
  })

  it('does not start crash detection when disabled', function() {
    const crash = require('@/lib/crash-detection')
    render(React.createElement(TestCase, { enabled: false }))
    expect(crash.startCrashDetection).not.toHaveBeenCalled()
  })

  it('stops crash detection on unmount', function() {
    const comp = render(React.createElement(TestCase, { enabled: true }))
    const crash = require('@/lib/crash-detection')
    comp.unmount()
    expect(crash.stopCrashDetection).toHaveBeenCalled()
  })

  it('passes stable callback to startCrashDetection', function() {
    render(React.createElement(TestCase, { enabled: true }))
    const crash = require('@/lib/crash-detection')
    expect(crash.startCrashDetection.mock.calls[0][0]).toEqual(expect.any(Function))
  })

  it('exposes simulateCrash function', function() {
    const el = render(React.createElement(TestCase, { enabled: true }))
    const div = el.container.querySelector('[data-simulate]')
    expect(div?.getAttribute('data-simulate')).toBe('function')
  })

  it('calls onCrashDetected callback when stableCallback is invoked', function() {
    const onCrash = jest.fn()
    render(React.createElement(TestCase, { onCrash: onCrash, enabled: true }))
    const crash = require('@/lib/crash-detection')
    const callback = crash.startCrashDetection.mock.calls[0][0]
    callback(9.8)
    expect(onCrash).toHaveBeenCalledWith(9.8)
  })
})
