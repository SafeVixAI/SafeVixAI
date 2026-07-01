import { render, act } from '@testing-library/react'
import React from 'react'
import { SentryInit } from '../providers/SentryInit'

describe('SentryInit', function() {
  it('renders nothing when no DSN', function() {
    var { container } = render(React.createElement(SentryInit))
    expect(container.innerHTML).toBe('')
  })

  it('renders as a fragment', function() {
    var { container } = render(React.createElement(SentryInit))
    expect(container.children.length).toBe(0)
  })

  it('creates sentry script element when DSN is set', function() {
    process.env.NEXT_PUBLIC_SENTRY_DSN = 'https://fake@dsn.ingest.sentry.io/123'
    var appendChildSpy = jest.spyOn(document.head, 'appendChild')
    render(React.createElement(SentryInit))
    var script = appendChildSpy.mock.calls[0][0] as HTMLScriptElement
    expect(script.src).toBe('https://browser.sentry-cdn.com/8.0.0/bundle.tracing.replay.min.js')
    expect(script.crossOrigin).toBe('anonymous')
    appendChildSpy.mockRestore()
    delete process.env.NEXT_PUBLIC_SENTRY_DSN
  })

  it('calls Sentry.init on script load', function() {
    process.env.NEXT_PUBLIC_SENTRY_DSN = 'https://fake@dsn.ingest.sentry.io/123'
    var mockSentry = { init: jest.fn(), replayIntegration: jest.fn().mockReturnValue({}) }
    ;(window as any).Sentry = mockSentry
    var appendChildSpy = jest.spyOn(document.head, 'appendChild')
    render(React.createElement(SentryInit))
    var script = appendChildSpy.mock.calls[0][0] as HTMLScriptElement
    act(function() { script.onload!(new Event('load')) })
    expect(mockSentry.init).toHaveBeenCalledWith({
      dsn: 'https://fake@dsn.ingest.sentry.io/123',
      environment: 'test',
      tracesSampleRate: 0.1,
      replaysSessionSampleRate: 0.1,
      replaysOnErrorSampleRate: 1.0,
      integrations: [{}],
    })
    appendChildSpy.mockRestore()
    delete process.env.NEXT_PUBLIC_SENTRY_DSN
    delete (window as any).Sentry
  })
})
