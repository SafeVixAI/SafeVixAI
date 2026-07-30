describe('rum', function () {
  let originalEnv
  let originalPerfObserver
  let originalWindow

  beforeEach(function () {
    originalEnv = process.env.NODE_ENV
    originalPerfObserver = global.PerformanceObserver
    originalWindow = global.window
    global.PerformanceObserver = jest.fn(function () { return { observe: jest.fn() } })
    global.performance = { getEntriesByType: jest.fn().mockReturnValue([]) }
  })

  afterEach(function () {
    process.env.NODE_ENV = originalEnv
    global.PerformanceObserver = originalPerfObserver
    global.window = originalWindow
  })

  it('does nothing on server side', async function () {
    delete global.window
    const mod = await import('../rum')
    expect(function () { mod.initRUM() }).not.toThrow()
  })

  it('creates observers for LCP, FID, CLS', async function () {
    const mod = await import('../rum')
    mod.initRUM()
    expect(global.PerformanceObserver).toHaveBeenCalled()
  })

  it('logs metrics in dev mode', async function () {
    process.env.NODE_ENV = 'development'
    const consoleSpy = jest.spyOn(console, 'log').mockImplementation()
    global.PerformanceObserver = jest.fn(function (cb) {
      return {
        observe: function () {
          const list = { getEntries: function () { return [{ startTime: 100 }] } }
          cb(list)
        }
      }
    })
    const mod = await import('../rum')
    mod.initRUM()
    expect(consoleSpy).toHaveBeenCalled()
    consoleSpy.mockRestore()
  })

  it('handles errors gracefully when PerformanceObserver throws', async function () {
    global.PerformanceObserver = jest.fn(function () { throw new Error('no perf') })
    const mod = await import('../rum')
    expect(function () { mod.initRUM() }).not.toThrow()
  })

  it('reports navigation timing when available', async function () {
    global.performance.getEntriesByType = jest.fn(function (type) {
      if (type === 'navigation') return [{ responseStart: 200, requestStart: 100, domContentLoadedEventEnd: 500, fetchStart: 50, loadEventEnd: 800 }]
      return []
    })
    const consoleSpy = jest.spyOn(console, 'log').mockImplementation()
    process.env.NODE_ENV = 'development'
    const mod = await import('../rum')
    mod.initRUM()
    expect(consoleSpy).toHaveBeenCalledWith('[RUM] TTFB: 100.00ms')
    expect(consoleSpy).toHaveBeenCalledWith('[RUM] DOM_LOAD: 450.00ms')
    expect(consoleSpy).toHaveBeenCalledWith('[RUM] FULL_LOAD: 750.00ms')
    consoleSpy.mockRestore()
  })

  it('calls observers in test mode but does not log', async function () {
    const consoleSpy = jest.spyOn(console, 'log').mockImplementation()
    global.PerformanceObserver = jest.fn(function (cb) {
      return {
        observe: function () {
          const list = { getEntries: function () { return [{ startTime: 42 }] } }
          cb(list)
        }
      }
    })
    const mod = await import('../rum')
    mod.initRUM()
    expect(consoleSpy).not.toHaveBeenCalled()
    consoleSpy.mockRestore()
  })

  it('does not log in production', async function () {
    process.env.NODE_ENV = 'production'
    const consoleSpy = jest.spyOn(console, 'log').mockImplementation()
    const mod = await import('../rum')
    mod.initRUM()
    expect(consoleSpy).not.toHaveBeenCalled()
    consoleSpy.mockRestore()
  })

  it('skips CLS entry when hadRecentInput is true', async function () {
    process.env.NODE_ENV = 'development'
    const consoleSpy = jest.spyOn(console, 'log').mockImplementation()
    let capturedCb
    global.PerformanceObserver = jest.fn(function (cb) {
      capturedCb = cb
      return { observe: jest.fn() }
    })
    const mod = await import('../rum')
    mod.initRUM()
    capturedCb({ getEntries: function () { return [{ hadRecentInput: true, value: 0.5 }] } })
    expect(consoleSpy).not.toHaveBeenCalledWith('[RUM] CLS: 0.50ms')
    consoleSpy.mockRestore()
  })

  it('reports CLS when hadRecentInput is false', async function () {
    process.env.NODE_ENV = 'development'
    const consoleSpy = jest.spyOn(console, 'log').mockImplementation()
    let capturedCb
    global.PerformanceObserver = jest.fn(function (cb) {
      capturedCb = cb
      return { observe: jest.fn() }
    })
    const mod = await import('../rum')
    mod.initRUM()
    capturedCb({ getEntries: function () { return [{ hadRecentInput: false, value: 0.3 }] } })
    expect(consoleSpy).toHaveBeenCalledWith('[RUM] CLS: 0.30ms')
    consoleSpy.mockRestore()
  })
})
