jest.mock('@/lib/api', function() { return { authFetch: jest.fn() } })
jest.mock('@/lib/geolocation', function() { return { useGeolocation: function() { return { location: null } } } })
jest.mock('@/lib/client-logger', function() { return { logClientError: jest.fn() } })
jest.mock('@/lib/offline-ai', function() { return { getOfflineAI: jest.fn(function() { return Promise.resolve() }), askOfflineAI: jest.fn(function() { return Promise.resolve('Offline reply') }) } })
jest.mock('@/lib/store', function() {
  const state = { aiMode: 'online', setAiMode: jest.fn(), authToken: null }
  return {
    useAppStore: function(selector: any) {
      if (typeof selector === 'function') return selector(state)
      return state
    },
    __setState: function(update: any) { Object.assign(state, update) },
  }
})
jest.mock('@/components/ConnectivityBadge', function() {
  return { ConnectivityBadge: function() { return null } }
})

jest.mock('lucide-react', function() {
  const React = require('react')
  return {
    Send: function() { return React.createElement('span', { 'data-testid': 'send-icon' }) },
    Loader2: function() { return React.createElement('span', { 'data-testid': 'loader-icon' }) },
    Wifi: function() { return React.createElement('span', { 'data-testid': 'wifi-icon' }) },
    WifiOff: function() { return React.createElement('span', { 'data-testid': 'wifi-off-icon' }) },
    Bot: function() { return React.createElement('span', { 'data-testid': 'bot-icon' }) },
    UserCircle: function() { return React.createElement('span', { 'data-testid': 'user-icon' }) },
  }
})

global.fetch = jest.fn()

import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import React from 'react'
import { ChatInterface } from '../ChatInterface'

describe('ChatInterface', function() {
  beforeEach(function() {
    jest.clearAllMocks()
    // JSDOM doesn't support scrollIntoView
    Element.prototype.scrollIntoView = jest.fn()
  })

  it('renders greeting message', function() {
    render(React.createElement(ChatInterface))
    expect(screen.getByText(/Hello!/)).toBeInTheDocument()
  })

  it('renders chat input', function() {
    render(React.createElement(ChatInterface))
    expect(screen.getByLabelText('Chat message input')).toBeInTheDocument()
  })

  it('renders send button', function() {
    render(React.createElement(ChatInterface))
    expect(screen.getByLabelText('Send message')).toBeInTheDocument()
  })

  it('renders mode toggle buttons', function() {
    render(React.createElement(ChatInterface))
    expect(screen.getByText('Online')).toBeInTheDocument()
    expect(screen.getByText('Offline')).toBeInTheDocument()
  })

  it('disables send button when input is empty', function() {
    render(React.createElement(ChatInterface))
    expect(screen.getByLabelText('Send message')).toBeDisabled()
  })

  it('enables send button when input has text', function() {
    render(React.createElement(ChatInterface))
    const input = screen.getByLabelText('Chat message input')
    fireEvent.change(input, { target: { value: 'Hello' } })
    expect(screen.getByLabelText('Send message')).not.toBeDisabled()
  })

  it('sends message on Enter key', function() {
    render(React.createElement(ChatInterface))
    const input = screen.getByLabelText('Chat message input')
    fireEvent.change(input, { target: { value: 'Hello' } })
    fireEvent.keyDown(input, { key: 'Enter', shiftKey: false })
    expect(screen.getByText('Hello')).toBeInTheDocument()
  })

  it('clears input after sending', function() {
    render(React.createElement(ChatInterface))
    const input = screen.getByLabelText('Chat message input') as HTMLInputElement
    fireEvent.change(input, { target: { value: 'Hello' } })
    fireEvent.keyDown(input, { key: 'Enter', shiftKey: false })
    expect(input.value).toBe('')
  })

  it('shows user message bubble with avatar', function() {
    render(React.createElement(ChatInterface))
    const input = screen.getByLabelText('Chat message input')
    fireEvent.change(input, { target: { value: 'Test message' } })
    fireEvent.keyDown(input, { key: 'Enter', shiftKey: false })
    expect(screen.getByText('Test message')).toBeInTheDocument()
  })

  it('shows offline placeholder text when in offline mode', function() {
    require('@/lib/store').__setState({ aiMode: 'offline' })
    render(React.createElement(ChatInterface))
    expect(screen.getByPlaceholderText(/offline mode/)).toBeInTheDocument()
  })

  it('shows online placeholder text when in online mode', function() {
    require('@/lib/store').__setState({ aiMode: 'online' })
    render(React.createElement(ChatInterface))
    expect(screen.getByPlaceholderText(/traffic rules/)).toBeInTheDocument()
  })

  it('handles fetch error in online mode', async function() {
    global.fetch = jest.fn(function() { return Promise.reject(new Error('Network error')) }) as jest.Mock
    render(React.createElement(ChatInterface))
    const input = screen.getByLabelText('Chat message input')
    fireEvent.change(input, { target: { value: 'Hi' } })
    fireEvent.keyDown(input, { key: 'Enter', shiftKey: false })
    await waitFor(function() {
      expect(screen.getByText(/Sorry, I encountered an error/)).toBeInTheDocument()
    })
  })

  it('handles non-ok response in online mode', async function() {
    global.fetch = jest.fn(function() { return Promise.resolve({ ok: false, status: 500 }) }) as jest.Mock
    render(React.createElement(ChatInterface))
    const input = screen.getByLabelText('Chat message input')
    fireEvent.change(input, { target: { value: 'Hi' } })
    fireEvent.keyDown(input, { key: 'Enter', shiftKey: false })
    await waitFor(function() {
      expect(screen.getByText(/Sorry, I encountered an error/)).toBeInTheDocument()
    })
  })

  it('sends message via offline mode', async function() {
    require('@/lib/store').__setState({ aiMode: 'offline' })
    render(React.createElement(ChatInterface))
    const input = screen.getByLabelText('Chat message input')
    fireEvent.change(input, { target: { value: 'Hello offline' } })
    fireEvent.keyDown(input, { key: 'Enter', shiftKey: false })
    await waitFor(function() {
      expect(screen.getByText('Offline reply')).toBeInTheDocument()
    })
  })

  it('handles offline mode error', async function() {
    require('@/lib/store').__setState({ aiMode: 'offline' })
    const askOfflineAI = require('@/lib/offline-ai').askOfflineAI
    askOfflineAI.mockRejectedValueOnce(new Error('Model error'))
    render(React.createElement(ChatInterface))
    const input = screen.getByLabelText('Chat message input')
    fireEvent.change(input, { target: { value: 'Hello' } })
    fireEvent.keyDown(input, { key: 'Enter', shiftKey: false })
    await waitFor(function() {
      expect(screen.getByText(/Sorry, I encountered an error/)).toBeInTheDocument()
    })
  })
})
