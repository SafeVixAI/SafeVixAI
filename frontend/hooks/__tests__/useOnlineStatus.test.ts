// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

import { renderHook, act } from '@testing-library/react'

function triggerOnline(val: boolean) {
  window.dispatchEvent(new Event(val ? 'online' : 'offline'))
}

beforeEach(function() {
  Object.defineProperty(navigator, 'onLine', { configurable: true, value: true })
})

afterEach(function() {
  jest.restoreAllMocks()
})

describe('useOnlineStatus', function() {
  it('returns true when navigator.onLine is true', function() {
    const { result } = renderHook(() => require('../useOnlineStatus').useOnlineStatus())
    expect(result.current).toBe(true)
  })

  it('returns false when navigator.onLine is false', function() {
    Object.defineProperty(navigator, 'onLine', { configurable: true, value: false })
    const { result } = renderHook(() => require('../useOnlineStatus').useOnlineStatus())
    expect(result.current).toBe(false)
  })

  it('updates to false on offline event', function() {
    const { result } = renderHook(() => require('../useOnlineStatus').useOnlineStatus())
    act(() => { triggerOnline(false) })
    expect(result.current).toBe(false)
  })

  it('updates to true on online event', function() {
    Object.defineProperty(navigator, 'onLine', { configurable: true, value: false })
    const { result } = renderHook(() => require('../useOnlineStatus').useOnlineStatus())
    act(() => { triggerOnline(true) })
    expect(result.current).toBe(true)
  })

  it('removes event listeners on unmount', function() {
    const addSpy = jest.spyOn(window, 'addEventListener')
    const removeSpy = jest.spyOn(window, 'removeEventListener')
    const { unmount } = renderHook(() => require('../useOnlineStatus').useOnlineStatus())
    expect(addSpy).toHaveBeenCalledWith('online', expect.any(Function))
    expect(addSpy).toHaveBeenCalledWith('offline', expect.any(Function))
    unmount()
    expect(removeSpy).toHaveBeenCalledWith('online', expect.any(Function))
    expect(removeSpy).toHaveBeenCalledWith('offline', expect.any(Function))
  })
})


