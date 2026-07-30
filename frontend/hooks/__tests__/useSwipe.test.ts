// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

import { renderHook } from '@testing-library/react'

function createTouchEvent(clientX: number, clientY: number, type: 'touchstart' | 'touchend') {
  return { touches: [{ clientX, clientY }], changedTouches: [{ clientX, clientY }] } as any
}

describe('useSwipe', function() {
  it('calls onSwipeRight when dx > 50 and horizontal', function() {
    const onSwipeRight = jest.fn()
    const { result } = renderHook(() => require('../useSwipe').useSwipe({ onSwipeRight }))
    result.current.onTouchStart(createTouchEvent(0, 0, 'touchstart'))
    result.current.onTouchEnd(createTouchEvent(100, 5, 'touchend'))
    expect(onSwipeRight).toHaveBeenCalled()
  })

  it('calls onSwipeLeft when dx < -50 and horizontal', function() {
    const onSwipeLeft = jest.fn()
    const { result } = renderHook(() => require('../useSwipe').useSwipe({ onSwipeLeft }))
    result.current.onTouchStart(createTouchEvent(100, 0, 'touchstart'))
    result.current.onTouchEnd(createTouchEvent(0, 5, 'touchend'))
    expect(onSwipeLeft).toHaveBeenCalled()
  })

  it('calls onSwipeDown when dy > 50 and vertical', function() {
    const onSwipeDown = jest.fn()
    const { result } = renderHook(() => require('../useSwipe').useSwipe({ onSwipeDown }))
    result.current.onTouchStart(createTouchEvent(0, 0, 'touchstart'))
    result.current.onTouchEnd(createTouchEvent(5, 100, 'touchend'))
    expect(onSwipeDown).toHaveBeenCalled()
  })

  it('calls onSwipeUp when dy < -50 and vertical', function() {
    const onSwipeUp = jest.fn()
    const { result } = renderHook(() => require('../useSwipe').useSwipe({ onSwipeUp }))
    result.current.onTouchStart(createTouchEvent(0, 100, 'touchstart'))
    result.current.onTouchEnd(createTouchEvent(5, 0, 'touchend'))
    expect(onSwipeUp).toHaveBeenCalled()
  })

  it('does not call handlers for short swipes below 50px threshold', function() {
    const onSwipeRight = jest.fn()
    const onSwipeLeft = jest.fn()
    const onSwipeUp = jest.fn()
    const onSwipeDown = jest.fn()
    const { result } = renderHook(() => require('../useSwipe').useSwipe({ onSwipeRight, onSwipeLeft, onSwipeUp, onSwipeDown }))
    result.current.onTouchStart(createTouchEvent(0, 0, 'touchstart'))
    result.current.onTouchEnd(createTouchEvent(30, 30, 'touchend'))
    expect(onSwipeRight).not.toHaveBeenCalled()
    expect(onSwipeLeft).not.toHaveBeenCalled()
    expect(onSwipeUp).not.toHaveBeenCalled()
    expect(onSwipeDown).not.toHaveBeenCalled()
  })

  it('returns onTouchStart and onTouchEnd handlers', function() {
    const { result } = renderHook(() => require('../useSwipe').useSwipe({}))
    expect(result.current).toHaveProperty('onTouchStart')
    expect(result.current).toHaveProperty('onTouchEnd')
    expect(typeof result.current.onTouchStart).toBe('function')
    expect(typeof result.current.onTouchEnd).toBe('function')
  })
})


