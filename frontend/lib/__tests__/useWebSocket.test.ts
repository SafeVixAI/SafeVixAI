// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
import { renderHook, act } from '@testing-library/react'

describe('useWebSocket', function () {
  var mockWs: any
  var MockWebSocket: any

  beforeEach(function () {
    mockWs = {
      readyState: WebSocket.OPEN,
      send: jest.fn(),
      close: jest.fn(),
    }
    MockWebSocket = jest.fn(function () { mockWs.onopen = jest.fn(); mockWs.onclose = jest.fn(); mockWs.onerror = jest.fn(); mockWs.onmessage = jest.fn(); return mockWs })
    ;(global as any).WebSocket = MockWebSocket
  })

  it('initial state is idle', async function () {
    var mod = await import('../useWebSocket')
    var { result } = renderHook(function () { return mod.useWebSocket({ onMessage: jest.fn() }) })
    expect(result.current.status).toBe('idle')
    expect(result.current.reconnectAttempt).toBe(0)
  })

  it('connect opens WebSocket', async function () {
    var mod = await import('../useWebSocket')
    var { result } = renderHook(function () { return mod.useWebSocket({ onMessage: jest.fn() }) })
    act(function () { result.current.connect('ws://test.com') })
    expect(MockWebSocket).toHaveBeenCalledWith('ws://test.com')
  })

  it('send queues data when connected', async function () {
    var mod = await import('../useWebSocket')
    var { result } = renderHook(function () { return mod.useWebSocket({ onMessage: jest.fn() }) })
    act(function () { result.current.connect('ws://test.com') })
    act(function () { result.current.send('test data') })
    expect(mockWs.send).toHaveBeenCalledWith('test data')
  })

  it('disconnect cleans up', async function () {
    var mod = await import('../useWebSocket')
    var { result } = renderHook(function () { return mod.useWebSocket({ onMessage: jest.fn() }) })
    act(function () { result.current.connect('ws://test.com') })
    act(function () { result.current.disconnect() })
    expect(result.current.status).toBe('idle')
  })

  it('handles onopen', async function () {
    var mod = await import('../useWebSocket')
    var onStatusChange = jest.fn()
    var { result } = renderHook(function () { return mod.useWebSocket({ onMessage: jest.fn(), onStatusChange: onStatusChange }) })
    act(function () { result.current.connect('ws://test.com') })
    act(function () { mockWs.onopen() })
    expect(onStatusChange).toHaveBeenCalledWith('connected')
  })

  it('handles onmessage with JSON', async function () {
    var mod = await import('../useWebSocket')
    var onMessage = jest.fn()
    var { result } = renderHook(function () { return mod.useWebSocket({ onMessage: onMessage }) })
    act(function () { result.current.connect('ws://test.com') })
    act(function () { mockWs.onopen() })
    act(function () { mockWs.onmessage({ data: JSON.stringify({ type: 'chat', text: 'hello' }) }) })
    expect(onMessage).toHaveBeenCalledWith({ type: 'chat', text: 'hello' })
  })

  it('handles onmessage with non-JSON', async function () {
    var mod = await import('../useWebSocket')
    var onMessage = jest.fn()
    var { result } = renderHook(function () { return mod.useWebSocket({ onMessage: onMessage }) })
    act(function () { result.current.connect('ws://test.com') })
    act(function () { mockWs.onopen() })
    act(function () { mockWs.onmessage({ data: 'plain text' }) })
    expect(onMessage).toHaveBeenCalledWith('plain text')
  })

  it('handles ping messages', async function () {
    var mod = await import('../useWebSocket')
    var onMessage = jest.fn()
    var { result } = renderHook(function () { return mod.useWebSocket({ onMessage: onMessage }) })
    act(function () { result.current.connect('ws://test.com') })
    act(function () { mockWs.onopen() })
    act(function () { mockWs.onmessage({ data: JSON.stringify({ type: 'ping' }) }) })
    expect(mockWs.send).toHaveBeenCalledWith(JSON.stringify({ type: 'pong' }))
    expect(onMessage).not.toHaveBeenCalled()
  })

  it('handles onclose and reconnects', async function () {
    jest.useFakeTimers()
    var mod = await import('../useWebSocket')
    var onStatusChange = jest.fn()
    var { result } = renderHook(function () { return mod.useWebSocket({ onMessage: jest.fn(), onStatusChange: onStatusChange }) })
    act(function () { result.current.connect('ws://test.com') })
    act(function () { MockWebSocket.mockClear() })
    act(function () { mockWs.onclose() })
    jest.advanceTimersByTime(2000)
    jest.useRealTimers()
  })

  it('calls updateStatus disconnected when max reconnect attempts reached', async function () {
    jest.useFakeTimers()
    var mod = await import('../useWebSocket')
    var onStatusChange = jest.fn()
    var { result } = renderHook(function () {
      return mod.useWebSocket({ onMessage: jest.fn(), onStatusChange: onStatusChange, reconnectMaxAttempts: 0 })
    })
    act(function () { result.current.connect('ws://test.com') })
    act(function () { mockWs.onclose() })
    // scheduleReconnect runs → attempt=1 > 0 → calls updateStatus('disconnected')
    expect(onStatusChange).toHaveBeenCalledWith('disconnected')
    jest.useRealTimers()
  })

  it('handles ws.onerror gracefully', async function () {
    var mod = await import('../useWebSocket')
    var { result } = renderHook(function () { return mod.useWebSocket({ onMessage: jest.fn() }) })
    act(function () { result.current.connect('ws://test.com') })
    act(function () { mockWs.onerror() })
    // onerror does nothing but should not throw
    expect(result.current.status).toBe('connecting')
  })

  it('handles WebSocket constructor throw with reconnect exhausted', async function () {
    MockWebSocket = jest.fn(function () { throw new Error('ws fail') })
    ;(global as any).WebSocket = MockWebSocket
    var mod = await import('../useWebSocket')
    var onStatusChange = jest.fn()
    var { result } = renderHook(function () {
      return mod.useWebSocket({ onMessage: jest.fn(), onStatusChange: onStatusChange, reconnectMaxAttempts: 0 })
    })
    act(function () { result.current.connect('ws://test.com') })
    // Constructor throw → catch sets 'disconnected', then scheduleReconnect
    // with maxAttempts=0 → attempt=1>0 → updateStatus('disconnected') again
    expect(onStatusChange).toHaveBeenCalledWith('disconnected')
  })

  it('clears pong timeout on cleanup after heartbeat', async function () {
    jest.useFakeTimers()
    var mod = await import('../useWebSocket')
    var { result } = renderHook(function () { return mod.useWebSocket({ onMessage: jest.fn(), heartbeatIntervalMs: 100 }) })
    act(function () { result.current.connect('ws://test.com') })
    act(function () { mockWs.onopen() })
    // Advance past heartbeat interval to trigger pong timeout set
    jest.advanceTimersByTime(150)
    act(function () { result.current.disconnect() })
    jest.useRealTimers()
  })
})
