// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

jest.mock('@gsap/react', function() {
  return { useGSAP: function() { return null } }
})
jest.mock('@/lib/gsap', function() {
  return { gsap: { fromTo: jest.fn(), to: jest.fn() } }
})

import { render, screen, fireEvent } from '@testing-library/react'
import React from 'react'
import { KeyboardShortcutsHelp } from '../ui/KeyboardShortcutsHelp'

describe('KeyboardShortcutsHelp', function() {
  it('is not visible initially', function() {
    const { container } = render(React.createElement(KeyboardShortcutsHelp))
    expect(container.innerHTML).toBe('')
  })

  it('opens when ? is pressed', function() {
    render(React.createElement(KeyboardShortcutsHelp))
    fireEvent.keyDown(document, { key: '?' })
    expect(screen.getByText('Keyboard Shortcuts')).toBeTruthy()
    expect(screen.getByText('Open command palette')).toBeTruthy()
    expect(screen.getByText('Close dialogs / Cancel SOS')).toBeTruthy()
  })

  it('closes when Escape is pressed', function() {
    render(React.createElement(KeyboardShortcutsHelp))
    fireEvent.keyDown(document, { key: '?' })
    expect(screen.getByRole('dialog')).toBeTruthy()
    fireEvent.keyDown(document, { key: 'Escape' })
    expect(screen.queryByRole('dialog')).toBeNull()
  })

  it('does not open when ? is pressed in an input', function() {
    render(React.createElement(KeyboardShortcutsHelp))
    const input = document.createElement('input')
    fireEvent.keyDown(input, { key: '?' })
    expect(screen.queryByText('Keyboard Shortcuts')).toBeNull()
  })

  it('does not open when ? is pressed with meta key', function() {
    render(React.createElement(KeyboardShortcutsHelp))
    fireEvent.keyDown(document, { key: '?', metaKey: true })
    expect(screen.queryByText('Keyboard Shortcuts')).toBeNull()
  })

  it('closes when overlay backdrop is clicked', function() {
    render(React.createElement(KeyboardShortcutsHelp))
    fireEvent.keyDown(document, { key: '?' })
    fireEvent.click(screen.getByRole('dialog'))
    expect(screen.queryByRole('dialog')).toBeNull()
  })
})
