import { render, screen, fireEvent, waitFor, act } from '@testing-library/react'
import React from 'react'

jest.mock('sonner', function () {
  return { toast: { error: jest.fn(), info: jest.fn(), success: jest.fn() } }
})

jest.mock('../crash/CrashCountdown', function () {
  var r = require('react')
  return { CrashCountdown: function CrashCountdownMock(props) {
    return r.createElement('div', { 'data-testid': 'crash-countdown' },
      r.createElement('span', { 'data-testid': 'crash-severity' }, props.severity),
      r.createElement('button', { 'data-testid': 'crash-cancel', onClick: props.onCancel }, 'Cancel'),
      r.createElement('button', { 'data-testid': 'crash-dispatch', onClick: props.onDispatch }, 'Dispatch'),
    )
  }}
})

jest.mock('@/lib/offline-sos-queue', function () {
  return { registerOfflineSyncListeners: jest.fn() }
})

jest.mock('@/lib/crash-detection', function () {
  return {
    startCrashDetection: jest.fn(),
    stopCrashDetection: jest.fn(),
  }
})

jest.mock('@/lib/safety-constants', function () {
  return { STANDARD_GRAVITY_MS2: 9.80665 }
})

describe('ClientAppHooks', function () {
  var crashHandler: Function

  beforeEach(function() {
    jest.clearAllMocks()
    crashHandler = function() {}
    var crashMod = require('@/lib/crash-detection')
    crashMod.startCrashDetection.mockImplementation(function(handler) {
      crashHandler = handler
      return Promise.resolve()
    })
  })

  it('renders without crashing', function () {
    var { container } = render(React.createElement(require('../ClientAppHooks').ClientAppHooks))
    expect(container).toBeDefined()
  })

  it('shows CrashCountdown when crash is detected', function () {
    render(React.createElement(require('../ClientAppHooks').ClientAppHooks))
    act(function() { crashHandler(147.09975) })
    expect(screen.getByTestId('crash-countdown')).toBeInTheDocument()
    expect(screen.getByTestId('crash-severity').textContent).toBe('severe')
  })

  it('calls handleCancel and hides crash on cancel', function () {
    render(React.createElement(require('../ClientAppHooks').ClientAppHooks))
    act(function() { crashHandler(147.09975) })
    fireEvent.click(screen.getByTestId('crash-cancel'))
    expect(screen.queryByTestId('crash-countdown')).not.toBeInTheDocument()
  })

  it('calls handleDispatch and hides crash on dispatch', function () {
    render(React.createElement(require('../ClientAppHooks').ClientAppHooks))
    act(function() { crashHandler(147.09975) })
    fireEvent.click(screen.getByTestId('crash-dispatch'))
    expect(screen.queryByTestId('crash-countdown')).not.toBeInTheDocument()
  })

  it('shows moderate severity for mid-range g-force', function () {
    render(React.createElement(require('../ClientAppHooks').ClientAppHooks))
    act(function() { crashHandler(98.0665) })
    expect(screen.getByTestId('crash-severity').textContent).toBe('moderate')
  })

  it('shows minor severity for low g-force', function () {
    render(React.createElement(require('../ClientAppHooks').ClientAppHooks))
    act(function() { crashHandler(9.80665) })
    expect(screen.getByTestId('crash-severity').textContent).toBe('minor')
  })

  it('shows toast error on crash detect', function () {
    var toast = require('sonner').toast
    render(React.createElement(require('../ClientAppHooks').ClientAppHooks))
    act(function() { crashHandler(147.09975) })
    expect(toast.error).toHaveBeenCalled()
  })

  it('calls registerOfflineSyncListeners', function () {
    var queue = require('@/lib/offline-sos-queue')
    render(React.createElement(require('../ClientAppHooks').ClientAppHooks))
    expect(queue.registerOfflineSyncListeners).toHaveBeenCalled()
  })
})
