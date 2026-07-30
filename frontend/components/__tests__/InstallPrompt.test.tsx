// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
import { render, screen, fireEvent, act } from '@testing-library/react'
import React from 'react'
import InstallPrompt from '../InstallPrompt'

function createBeforeInstallPromptEvent() {
  return new Event('beforeinstallprompt', { cancelable: true }) as any
}

function createMockBeforeInstallPromptEvent() {
  const userChoice = Promise.resolve({ outcome: 'accepted' as const })
  const promptFn = jest.fn()
  const event = new Event('beforeinstallprompt', { cancelable: true })
  Object.defineProperties(event, {
    prompt: { value: promptFn, writable: true },
    userChoice: { value: userChoice, writable: true },
  })
  return { event, promptFn, userChoice }
}

describe('InstallPrompt', function () {
  beforeEach(function () {
    jest.clearAllMocks()
    const swTarget = new EventTarget()
    Object.defineProperty(navigator, 'serviceWorker', {
      get: function() { return swTarget },
      configurable: true,
    })
  })

  it('returns null when not prompted', function () {
    const container = render(React.createElement(InstallPrompt, null))
    expect(container.container.innerHTML).toBe('')
  })

  it('registers event listeners on mount', function () {
    const addEventListener = jest.spyOn(window, 'addEventListener')
    render(React.createElement(InstallPrompt, null))
    expect(addEventListener).toHaveBeenCalledWith('beforeinstallprompt', expect.any(Function))
    expect(addEventListener).toHaveBeenCalledWith('appinstalled', expect.any(Function))
    addEventListener.mockRestore()
  })

  it('shows install banner after beforeinstallprompt event', function () {
    render(React.createElement(InstallPrompt, null))
    const { event } = createMockBeforeInstallPromptEvent()
    act(function () { window.dispatchEvent(event) })
    expect(screen.getByText(/Install SafeVixAI/i)).toBeTruthy()
    expect(screen.getByText(/offline access/i)).toBeTruthy()
    expect(screen.getByRole('button', { name: 'Install' })).toBeTruthy()
  })

  it('calls prompt on Install button click', async function () {
    render(React.createElement(InstallPrompt, null))
    const { event, promptFn } = createMockBeforeInstallPromptEvent()
    act(function () { window.dispatchEvent(event) })
    fireEvent.click(screen.getByRole('button', { name: 'Install' }))
    expect(promptFn).toHaveBeenCalledTimes(1)
  })

  it('prevents default on beforeinstallprompt', function () {
    render(React.createElement(InstallPrompt, null))
    const event = createBeforeInstallPromptEvent()
    const preventDefaultSpy = jest.spyOn(event, 'preventDefault')
    window.dispatchEvent(event)
    expect(preventDefaultSpy).toHaveBeenCalled()
  })

  it('hides banner on dismiss button click', function () {
    render(React.createElement(InstallPrompt, null))
    const { event } = createMockBeforeInstallPromptEvent()
    act(function () { window.dispatchEvent(event) })
    expect(screen.getByText(/Install SafeVixAI/i)).toBeTruthy()
    fireEvent.click(screen.getByLabelText(/Dismiss/i))
    expect(screen.queryByText(/Install SafeVixAI/i)).toBeNull()
  })

  it('re-registers beforeinstallprompt listener with new dismissed value', function () {
    const removeListener = jest.spyOn(window, 'removeEventListener')
    render(React.createElement(InstallPrompt, null))
    const { event } = createMockBeforeInstallPromptEvent()
    act(function () { window.dispatchEvent(event) })
    fireEvent.click(screen.getByLabelText(/Dismiss/i))
    expect(removeListener).toHaveBeenCalledWith('beforeinstallprompt', expect.any(Function))
    removeListener.mockRestore()
  })

  it('hides banner when appinstalled event fires', function () {
    const toastSpy = { success: jest.fn() }
    jest.mock('sonner', function () { return { toast: toastSpy } })
    render(React.createElement(InstallPrompt, null))
    const { event } = createMockBeforeInstallPromptEvent()
    act(function () { window.dispatchEvent(event) })
    expect(screen.getByText(/Install SafeVixAI/i)).toBeTruthy()
    act(function () { window.dispatchEvent(new Event('appinstalled')) })
    expect(screen.queryByText(/Install SafeVixAI/i)).toBeNull()
  })

  it('hides banner on service worker APP_INSTALLED message', function () {
    render(React.createElement(InstallPrompt, null))
    const { event } = createMockBeforeInstallPromptEvent()
    act(function () { window.dispatchEvent(event) })
    expect(screen.getByText(/Install SafeVixAI/i)).toBeTruthy()
    act(function () {
      const msgEvent = new MessageEvent('message', { data: { type: 'APP_INSTALLED' } })
      navigator.serviceWorker?.dispatchEvent(msgEvent)
    })
    expect(screen.queryByText(/Install SafeVixAI/i)).toBeNull()
  })
})
