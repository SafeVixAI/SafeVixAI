// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

import { render, screen, fireEvent, act } from '@testing-library/react'
import React from 'react'

beforeEach(function() {
  document.body.innerHTML = ''
})

afterEach(function() {
  jest.restoreAllMocks()
})

function TestCase({ active }: { active: boolean }) {
  const ref = require('../useFocusTrap').useFocusTrap(active)
  return React.createElement('div', { ref, 'data-testid': 'trap' },
    React.createElement('button', { 'data-testid': 'first' }, 'First'),
    React.createElement('button', { 'data-testid': 'last' }, 'Last'),
  )
}

describe('useFocusTrap', function() {
  it('focuses the first focusable element when activated', function() {
    render(React.createElement(TestCase, { active: true }))
    expect(document.activeElement).toBe(screen.getByTestId('first'))
  })

  it('wraps Tab from last to first element', function() {
    render(React.createElement(TestCase, { active: true }))
    const last = screen.getByTestId('last')
    last.focus()
    const evt = new KeyboardEvent('keydown', { key: 'Tab', bubbles: true })
    jest.spyOn(evt, 'preventDefault')
    act(() => { screen.getByTestId('trap').dispatchEvent(evt) })
    expect(evt.preventDefault).toHaveBeenCalled()
    expect(document.activeElement).toBe(screen.getByTestId('first'))
  })

  it('wraps Shift+Tab from first to last element', function() {
    render(React.createElement(TestCase, { active: true }))
    const first = screen.getByTestId('first')
    first.focus()
    const evt = new KeyboardEvent('keydown', { key: 'Tab', shiftKey: true, bubbles: true })
    jest.spyOn(evt, 'preventDefault')
    act(() => { screen.getByTestId('trap').dispatchEvent(evt) })
    expect(evt.preventDefault).toHaveBeenCalled()
    expect(document.activeElement).toBe(screen.getByTestId('last'))
  })

  it('does nothing on non-Tab keypress', function() {
    render(React.createElement(TestCase, { active: true }))
    const evt = new KeyboardEvent('keydown', { key: 'Escape', bubbles: true })
    jest.spyOn(evt, 'preventDefault')
    act(() => { screen.getByTestId('trap').dispatchEvent(evt) })
    expect(evt.preventDefault).not.toHaveBeenCalled()
  })

  it('does not run when active is false', function() {
    render(React.createElement(TestCase, { active: false }))
    expect(document.activeElement).not.toBe(screen.getByTestId('first'))
  })

  it('restores previous focus on unmount', function() {
    const outside = document.createElement('button')
    outside.id = 'outside'
    document.body.appendChild(outside)
    outside.focus()
    expect(document.activeElement).toBe(outside)
    const { unmount } = render(React.createElement(TestCase, { active: true }))
    unmount()
    expect(document.activeElement).toBe(outside)
  })
})


