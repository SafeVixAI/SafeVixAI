// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

import { render, screen, act } from '@testing-library/react'
import React from 'react'
import { ServerHealthStatus } from '../ServerHealthStatus'

describe('ServerHealthStatus', function() {
  beforeEach(function() {
    var mockFetch = jest.fn().mockResolvedValue({ ok: true, json: function() { return Promise.resolve({ database_available: true }) } })
    global.fetch = mockFetch as any
  })

  afterEach(function() {
    delete (global as any).fetch
  })

  it('shows checking status on initial render', function() {
    render(React.createElement(ServerHealthStatus))
    expect(screen.getByText('API')).toBeTruthy()
    expect(screen.getByText('AI')).toBeTruthy()
  })

  it('toggles expanded panel on button click', function() {
    render(React.createElement(ServerHealthStatus))
    var btn = screen.getByTitle('Server health status')
    act(function() { btn.click() })
    expect(screen.getByText('Backend')).toBeTruthy()
    expect(screen.getByText('Database')).toBeTruthy()
    expect(screen.getByText('Chatbot AI')).toBeTruthy()
  })

  it('closes expanded panel on second click', function() {
    render(React.createElement(ServerHealthStatus))
    var btn = screen.getByTitle('Server health status')
    act(function() { btn.click() })
    expect(screen.getByText('Backend')).toBeTruthy()
    act(function() { btn.click() })
    expect(screen.queryByText('Backend')).toBeNull()
  })

  it('shows offline status when backend json parse fails', async function() {
    global.fetch = jest.fn().mockResolvedValue({ ok: true, json: function() { return Promise.reject(new Error('invalid json')) } } as any)
    render(React.createElement(ServerHealthStatus))
    await new Promise(function(r) { return setTimeout(r, 50) })
    act(function() { screen.getByTitle('Server health status').click() })
    expect(screen.getByText('Offline')).toBeTruthy()
  })

  it('shows offline when backend returns not ok', async function() {
    global.fetch = jest.fn().mockResolvedValue({ ok: false } as any)
    render(React.createElement(ServerHealthStatus))
    await new Promise(function(r) { return setTimeout(r, 50) })
    act(function() { screen.getByTitle('Server health status').click() })
    expect(screen.getAllByText('Offline').length).toBeGreaterThanOrEqual(2)
  })

  it('shows database offline when database_available is false', async function() {
    global.fetch = jest.fn().mockResolvedValue({ ok: true, json: function() { return Promise.resolve({ database_available: false }) } } as any)
    render(React.createElement(ServerHealthStatus))
    await new Promise(function(r) { return setTimeout(r, 50) })
    act(function() { screen.getByTitle('Server health status').click() })
    expect(screen.getByText('Offline')).toBeTruthy()
  })
})
