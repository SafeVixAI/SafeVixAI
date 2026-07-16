var mockStoreState = { crashDetectionEnabled: true, setCrashDetectionEnabled: jest.fn() }

jest.mock('@/lib/store', function() {
  var storeHook = function(selector: any) {
    return typeof selector === 'function' ? selector(mockStoreState) : mockStoreState
  }
  return {
    useAppStore: Object.assign(storeHook, { getState: jest.fn(function() { return mockStoreState }) }),
  }
}, { virtual: false })

jest.mock('@/lib/features', function() {
  return { FEATURES: { crashDetection: true } }
}, { virtual: false })

jest.mock('@/lib/safety-constants', function() {
  return { STANDARD_GRAVITY_MS2: 9.81 }
}, { virtual: false })

jest.mock('@/hooks/useCrashDetection', function() {
  return { useCrashDetection: jest.fn() }
}, { virtual: false })

jest.mock('@/lib/analytics', function() {
  return { track: { crashDetected: jest.fn() } }
}, { virtual: false })

jest.mock('sonner', function() {
  return { toast: { info: jest.fn(), success: jest.fn(), error: jest.fn() }, Toaster: jest.fn(function() { return null }) }
}, { virtual: false })

import React from 'react'
import { renderHook, act } from '@testing-library/react'

var crashDetectionMod: any
var analyticsMod: any

beforeEach(function() {
  jest.clearAllMocks()
  crashDetectionMod = require('@/hooks/useCrashDetection')
  analyticsMod = require('@/lib/analytics')
})

function renderEnhancedCrashDetection() {
  var hookMod = require('../useEnhancedCrashDetection')
  return renderHook(function() { return hookMod.useEnhancedCrashDetection() })
}

describe('useEnhancedCrashDetection', function() {
  it('uses useCrashDetection with enabled flag', function() {
    renderEnhancedCrashDetection()
    expect(crashDetectionMod.useCrashDetection).toHaveBeenCalledWith(expect.objectContaining({ enabled: true }))
  })

  it('returns null crashState and clearCrashState function', function() {
    var { result } = renderEnhancedCrashDetection()
    expect(result.current.crashState).toBeNull()
    expect(typeof result.current.clearCrashState).toBe('function')
  })

  it('clearCrashState clears crashState after crash', function() {
    var { result } = renderEnhancedCrashDetection()
    var callback = crashDetectionMod.useCrashDetection.mock.calls[0][0].onCrashDetected
    act(function() { callback(147.15) })
    expect(result.current.crashState).toEqual({ force: 147.15, severity: 'severe' })
    act(function() { result.current.clearCrashState() })
    expect(result.current.crashState).toBeNull()
  })

  it('handleCrashDetected calculates severe (>=15G)', function() {
    renderEnhancedCrashDetection()
    var callback = crashDetectionMod.useCrashDetection.mock.calls[0][0].onCrashDetected
    act(function() { callback(147.15) })
    expect(analyticsMod.track.crashDetected).toHaveBeenCalledWith('impact', expect.closeTo(15, 5))
  })

  it('handleCrashDetected calculates moderate (>=10G)', function() {
    renderEnhancedCrashDetection()
    var callback = crashDetectionMod.useCrashDetection.mock.calls[0][0].onCrashDetected
    act(function() { callback(98.1) })
    expect(analyticsMod.track.crashDetected).toHaveBeenCalledWith('impact', expect.closeTo(10, 5))
  })

  it('handleCrashDetected calculates minor (<10G)', function() {
    renderEnhancedCrashDetection()
    var callback = crashDetectionMod.useCrashDetection.mock.calls[0][0].onCrashDetected
    act(function() { callback(49.05) })
    expect(analyticsMod.track.crashDetected).toHaveBeenCalledWith('impact', expect.closeTo(5, 5))
  })
})
