jest.mock('@/lib/rum', function() {
  return { initRUM: jest.fn() }
}, { virtual: false })

jest.mock('@/lib/offline-sos-queue', function() {
  return { registerOfflineSyncListeners: jest.fn() }
}, { virtual: false })

jest.mock('@/lib/client-logger', function() {
  return { logClientError: jest.fn() }
}, { virtual: false })

import { render, waitFor } from '@testing-library/react'
import React from 'react'

let rumMod: any
let offlineMod: any
let loggerMod: any

beforeEach(function() {
  jest.clearAllMocks()
  rumMod = require('@/lib/rum')
  offlineMod = require('@/lib/offline-sos-queue')
  loggerMod = require('@/lib/client-logger')
})

function TestCase() {
  require('../useClientServiceWorker').useClientServiceWorker()
  return React.createElement('div')
}

describe('useClientServiceWorker', function() {
  it('calls initRUM on mount', function() {
    render(React.createElement(TestCase))
    expect(rumMod.initRUM).toHaveBeenCalledTimes(1)
  })

  it('calls registerOfflineSyncListeners on mount', function() {
    render(React.createElement(TestCase))
    expect(offlineMod.registerOfflineSyncListeners).toHaveBeenCalledTimes(1)
  })

  it('does not error when serviceWorker is not available', function() {
    render(React.createElement(TestCase))
    expect(loggerMod.logClientError).not.toHaveBeenCalled()
  })

  it('registers SW when serviceWorker is available', function() {
    const mockRegister = jest.fn().mockResolvedValue({ scope: '/' })
    ;(navigator as any).serviceWorker = { register: mockRegister }
    render(React.createElement(TestCase))
    expect(mockRegister).toHaveBeenCalledWith('/sw.js')
    delete (navigator as any).serviceWorker
  })

  it('calls logClientError on SW registration failure', async function() {
    const swError = new Error('SW failed')
    ;(navigator as any).serviceWorker = { register: jest.fn().mockRejectedValue(swError) }
    render(React.createElement(TestCase))
    await waitFor(function() {
      expect(loggerMod.logClientError).toHaveBeenCalledWith('ServiceWorker registration failed', swError)
    })
    delete (navigator as any).serviceWorker
  })
})
