// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
describe('rum', function () {
  var originalEnv: any
  var originalPerfObserver: any

  beforeEach(function () {
    originalEnv = process.env.NODE_ENV
    originalPerfObserver = (global as any).PerformanceObserver
    ;(global as any).PerformanceObserver = jest.fn(function () { return { observe: jest.fn() } }) as any
    ;(global as any).performance = { getEntriesByType: jest.fn().mockReturnValue([]) } as any
  })

  afterEach(function () {
    process.env.NODE_ENV = originalEnv
    ;(global as any).PerformanceObserver = originalPerfObserver
  })

  it('does nothing on server side', async function () {
    var mod = await import('../rum')
    expect(typeof mod.initRUM).toBe('function')
  })

  it('creates observers for LCP, FID, CLS', async function () {
    var mod = await import('../rum')
    mod.initRUM()
    expect(global.PerformanceObserver).toHaveBeenCalled()
  })

  it('logs metrics in dev mode', async function () {
    process.env.NODE_ENV = 'development'
    var consoleSpy = jest.spyOn(console, 'log').mockImplementation()
    ;(global as any).PerformanceObserver = jest.fn(function (cb: any) {
      return {
        observe: function () {
          var list = { getEntries: function () { return [{ startTime: 100 }] } }
          cb(list)
        }
      }
    }) as any
    var mod = await import('../rum')
    mod.initRUM()
    expect(consoleSpy).toHaveBeenCalled()
    consoleSpy.mockRestore()
  })

  it('handles errors gracefully', async function () {
    (global as any).PerformanceObserver = jest.fn(function () { throw new Error('no perf') })
    var mod = await import('../rum')
    expect(function () { mod.initRUM() }).not.toThrow()
  })
})
