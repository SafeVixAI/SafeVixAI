// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
var origDeviceMotion = (globalThis as any).DeviceMotionEvent

describe('crash-detection', function () {
  beforeEach(function () {
    jest.resetModules()
    if (typeof DeviceMotionEvent === 'undefined') {
      (globalThis as any).DeviceMotionEvent = function () {} as any
    }
  })

  afterAll(function () {
    (globalThis as any).DeviceMotionEvent = origDeviceMotion
  })

  // ── startCrashDetection ──

  it('startCrashDetection no-ops when DeviceMotionEvent undefined', async function () {
    (globalThis as any).DeviceMotionEvent = undefined
    var mod = await import('../crash-detection')
    var cb = jest.fn()
    expect(function () { mod.startCrashDetection(cb) }).not.toThrow()
  })

  it('startCrashDetection registers listener and callback', async function () {
    var mod = await import('../crash-detection')
    var cb = jest.fn()
    mod.startCrashDetection(cb)
    mod.simulateCrashDemo()
    expect(cb).toHaveBeenCalled()
  })

  it('startCrashDetection deduplicates same callback', async function () {
    var addEventListener = jest.spyOn(window, 'addEventListener')
    var mod = await import('../crash-detection')
    var cb = jest.fn()
    mod.startCrashDetection(cb)
    mod.startCrashDetection(cb)
    expect(addEventListener).toHaveBeenCalledTimes(1)
    addEventListener.mockRestore()
  })

  it('startCrashDetection does not register second listener with different callbacks', async function () {
    var addEventListener = jest.spyOn(window, 'addEventListener')
    var mod = await import('../crash-detection')
    mod.startCrashDetection(jest.fn())
    mod.startCrashDetection(jest.fn())
    expect(addEventListener).toHaveBeenCalledTimes(1)
    addEventListener.mockRestore()
  })

  // ── stopCrashDetection ──

  it('stopCrashDetection removes listener when no callbacks remain', async function () {
    var removeEventListener = jest.spyOn(window, 'removeEventListener')
    var mod = await import('../crash-detection')
    var cb = jest.fn()
    mod.startCrashDetection(cb)
    mod.stopCrashDetection(cb)
    expect(removeEventListener).toHaveBeenCalled()
    removeEventListener.mockRestore()
  })

  it('stopCrashDetection keeps listener when other callbacks remain', async function () {
    var removeEventListener = jest.spyOn(window, 'removeEventListener')
    var mod = await import('../crash-detection')
    var cb1 = jest.fn()
    var cb2 = jest.fn()
    mod.startCrashDetection(cb1)
    mod.startCrashDetection(cb2)
    mod.stopCrashDetection(cb1)
    expect(removeEventListener).not.toHaveBeenCalled()
    removeEventListener.mockRestore()
  })

  // ── simulateCrashDemo ──

  it('simulateCrashDemo does not double-trigger while debouncing', async function () {
    var mod = await import('../crash-detection')
    var cb = jest.fn()
    mod.startCrashDetection(cb)
    mod.simulateCrashDemo()
    mod.simulateCrashDemo()
    expect(cb).toHaveBeenCalledTimes(1)
  })

  it('simulateCrashDemo triggers again after debounce', async function () {
    jest.useFakeTimers()
    var mod = await import('../crash-detection')
    var cb = jest.fn()
    mod.startCrashDetection(cb)
    mod.simulateCrashDemo()
    jest.advanceTimersByTime(61000)
    mod.simulateCrashDemo()
    expect(cb).toHaveBeenCalledTimes(2)
    jest.useRealTimers()
  })

  // ── requestCrashPermission ──

  it('requestCrashPermission returns false when DeviceMotionEvent undefined', async function () {
    (globalThis as any).DeviceMotionEvent = undefined
    var mod = await import('../crash-detection')
    var result = await mod.requestCrashPermission()
    expect(result).toBe(false)
  })

  it('requestCrashPermission returns true when no permission API', async function () {
    var mod = await import('../crash-detection')
    var result = await mod.requestCrashPermission()
    expect(result).toBe(true)
  })

  it('requestCrashPermission returns true when granted', async function () {
    (globalThis as any).DeviceMotionEvent = {
      requestPermission: function () { return Promise.resolve('granted') },
    }
    var mod = await import('../crash-detection')
    var result = await mod.requestCrashPermission()
    expect(result).toBe(true)
  })

  it('requestCrashPermission returns false when denied', async function () {
    (globalThis as any).DeviceMotionEvent = {
      requestPermission: function () { return Promise.resolve('denied') },
    }
    var mod = await import('../crash-detection')
    var result = await mod.requestCrashPermission()
    expect(result).toBe(false)
  })

  it('requestCrashPermission catches errors', async function () {
    (globalThis as any).DeviceMotionEvent = {
      requestPermission: function () { return Promise.reject(new Error('permission error')) },
    }
    var mod = await import('../crash-detection')
    var result = await mod.requestCrashPermission()
    expect(result).toBe(false)
  })

  // ── handleDeviceMotion (tested via stubs) ──

  it('handleDeviceMotion ignores events when no crash detected', function (done) {
    jest.isolateModules(function () {
      var origEventListener = window.addEventListener
      var capturedHandler: any = null
      window.addEventListener = function (type: string, handler: any, opts?: any) {
        if (type === 'devicemotion') capturedHandler = handler
      }
      var mod = require('../crash-detection')
      var cb = jest.fn()
      mod.startCrashDetection(cb)
      if (capturedHandler) {
        capturedHandler({ accelerationIncludingGravity: { x: 0, y: 0, z: 9.8 } })
      }
      expect(cb).not.toHaveBeenCalled()
      window.addEventListener = origEventListener
      done()
    })
  })

  it('handleDeviceMotion triggers callback on high G-force', function (done) {
    jest.isolateModules(function () {
      var origEventListener = window.addEventListener
      var capturedHandler: any = null
      window.addEventListener = function (type: string, handler: any, opts?: any) {
        if (type === 'devicemotion') capturedHandler = handler
      }
      var mod = require('../crash-detection')
      var cb = jest.fn()
      mod.startCrashDetection(cb)
      if (capturedHandler) {
        // high-G event (>15G = >147.15 m/s^2)
        capturedHandler({ accelerationIncludingGravity: { x: 0, y: 200, z: 0 } })
      }
      expect(cb).toHaveBeenCalled()
      window.addEventListener = origEventListener
      done()
    })
  })

  it('handleDeviceMotion resets crash flag after debounce', function (done) {
    jest.useFakeTimers()
    jest.isolateModules(function () {
      var origEventListener = window.addEventListener
      var capturedHandler: any = null
      window.addEventListener = function (type: string, handler: any, opts?: any) {
        if (type === 'devicemotion') capturedHandler = handler
      }
      var mod = require('../crash-detection')
      var cb = jest.fn()
      mod.startCrashDetection(cb)
      if (capturedHandler) {
        capturedHandler({ accelerationIncludingGravity: { x: 0, y: 200, z: 0 } })
      }
      expect(cb).toHaveBeenCalledTimes(1)
      jest.advanceTimersByTime(61000)
      if (capturedHandler) {
        capturedHandler({ accelerationIncludingGravity: { x: 0, y: 200, z: 0 } })
      }
      expect(cb).toHaveBeenCalledTimes(2)
      window.addEventListener = origEventListener
      done()
    })
    jest.useRealTimers()
  })

  it('handleDeviceMotion ignores missing accelerationIncludingGravity', function (done) {
    jest.isolateModules(function () {
      var origEventListener = window.addEventListener
      var capturedHandler: any = null
      window.addEventListener = function (type: string, handler: any, opts?: any) {
        if (type === 'devicemotion') capturedHandler = handler
      }
      var mod = require('../crash-detection')
      var cb = jest.fn()
      mod.startCrashDetection(cb)
      if (capturedHandler) capturedHandler({} as DeviceMotionEvent)
      expect(cb).not.toHaveBeenCalled()
      window.addEventListener = origEventListener
      done()
    })
  })
})
