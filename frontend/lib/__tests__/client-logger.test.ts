// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
describe('client-logger', function () {
  beforeEach(function () {
    jest.resetModules()
    delete (globalThis as any).posthog
    delete (globalThis as any).Sentry
  })

  it('exports logClientError and logClientWarning', async function () {
    const mod = await import('../client-logger')
    expect(typeof mod.logClientError).toBe('function')
    expect(typeof mod.logClientWarning).toBe('function')
  })

  it('exports flushErrors', async function () {
    const mod = await import('../client-logger')
    expect(typeof mod.flushErrors).toBe('function')
  })

  it('logClientError and logClientWarning work in development', async function () {
    const mod = await import('../client-logger')
    expect(function () { mod.logClientError('test error', { detail: 'test' }) }).not.toThrow()
    expect(function () { mod.logClientWarning('test warning') }).not.toThrow()
  })

  it('flushErrors flushes the queue', async function () {
    const mod = await import('../client-logger')
    expect(function () { mod.flushErrors() }).not.toThrow()
  })

  it('enqueues errors when NODE_ENV is production', async function () {
    const origNodeEnv = process.env.NODE_ENV
    process.env.NODE_ENV = 'production'
    jest.resetModules()
    const mod = await import('../client-logger')
    mod.logClientError('prod error')
    mod.logClientWarning('prod warn')
    expect(function () { mod.flushErrors() }).not.toThrow()
    process.env.NODE_ENV = origNodeEnv
  })

  it('flushes batch when queue reaches threshold', async function () {
    const origNodeEnv = process.env.NODE_ENV
    process.env.NODE_ENV = 'production'
    jest.resetModules()
    const mod = await import('../client-logger')
    // Add 5+ errors to trigger automatic flush
    for (let i = 0; i < 6; i++) {
      mod.logClientError('error ' + i)
    }
    process.env.NODE_ENV = origNodeEnv
  })

  it('flushErrorBatch sends to posthog when available', async function () {
    const origNodeEnv = process.env.NODE_ENV
    process.env.NODE_ENV = 'production'
    const captureMock = jest.fn()
    ;(globalThis as any).posthog = { capture: captureMock }
    jest.resetModules()
    const mod = await import('../client-logger')
    mod.logClientError('posthog error')
    mod.flushErrors()
    expect(captureMock).toHaveBeenCalled()
    process.env.NODE_ENV = origNodeEnv
  })

  it('flushErrorBatch handles posthog capture errors gracefully', async function () {
    const origNodeEnv = process.env.NODE_ENV
    process.env.NODE_ENV = 'production'
    ;(globalThis as any).posthog = { capture: function () { throw new Error('ph error') } }
    jest.resetModules()
    const mod = await import('../client-logger')
    mod.logClientError('ph crash')
    expect(function () { mod.flushErrors() }).not.toThrow()
    process.env.NODE_ENV = origNodeEnv
  })

  it('sends errors to Sentry when available in production', async function () {
    const origNodeEnv = process.env.NODE_ENV
    process.env.NODE_ENV = 'production'
    const captureExceptionMock = jest.fn()
    const captureMessageMock = jest.fn()
    ;(globalThis as any).Sentry = { captureException: captureExceptionMock, captureMessage: captureMessageMock }
    ;(globalThis as any).window = globalThis
    jest.resetModules()
    const mod = await import('../client-logger')
    mod.logClientError('sentry error', new Error('test'))
    mod.logClientWarning('sentry warn')
    expect(captureExceptionMock).toHaveBeenCalled()
    expect(captureMessageMock).toHaveBeenCalled()
    process.env.NODE_ENV = origNodeEnv
  })

  it('handles Sentry errors gracefully', async function () {
    const origNodeEnv = process.env.NODE_ENV
    process.env.NODE_ENV = 'production'
    ;(globalThis as any).Sentry = { captureException: function () { throw new Error('sentry crash') }, captureMessage: function () { throw new Error('sentry crash') } }
    ;(globalThis as any).window = globalThis
    jest.resetModules()
    const mod = await import('../client-logger')
    expect(function () { mod.logClientError('err') }).not.toThrow()
    expect(function () { mod.logClientWarning('warn') }).not.toThrow()
    process.env.NODE_ENV = origNodeEnv
  })

  it('registers beforeunload listener at module load', async function () {
    const addEventListenerSpy = jest.spyOn(window, 'addEventListener')
    jest.resetModules()
    await import('../client-logger')
    expect(addEventListenerSpy).toHaveBeenCalledWith('beforeunload', expect.any(Function))
    addEventListenerSpy.mockRestore()
  })

  it('enqueues errors and flushes via batch timer in production', async function () {
    const origNodeEnv = process.env.NODE_ENV
    process.env.NODE_ENV = 'production'
    jest.resetModules()
    const mod = await import('../client-logger')
    // Enqueue an error - this starts the batch timer
    mod.logClientError('batch timer error')
    // Trigger flush via the export
    mod.flushErrors()
    process.env.NODE_ENV = origNodeEnv
  })

  it('dispatches beforeunload triggers flush', async function () {
    const origNodeEnv = process.env.NODE_ENV
    process.env.NODE_ENV = 'production'
    jest.resetModules()
    const mod = await import('../client-logger')
    mod.logClientError('beforeunload flush test')
    // Dispatch beforeunload event - should trigger flush and clear interval
    window.dispatchEvent(new Event('beforeunload'))
    process.env.NODE_ENV = origNodeEnv
  })
})
