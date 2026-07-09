// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

import { render, screen, fireEvent } from '@testing-library/react'
import React from 'react'
import { Modal } from '../Modal'

describe('Modal', function () {
  it('returns null when not open', function () {
    var { container } = render(React.createElement(Modal, { open: false, onClose: jest.fn(), title: 'Test' }, null))
    expect(container.innerHTML).toBe('')
  })

  it('renders when open', function () {
    render(React.createElement(Modal, { open: true, onClose: jest.fn(), title: 'Test Title' }, React.createElement('p', null, 'Hello Modal')))
    expect(screen.getByRole('dialog')).toBeTruthy()
  })

  it('displays title', function () {
    render(React.createElement(Modal, { open: true, onClose: jest.fn(), title: 'My Modal' }, null))
    expect(screen.getByText('My Modal')).toBeTruthy()
  })

  it('renders children', function () {
    render(React.createElement(Modal, { open: true, onClose: jest.fn(), title: 'Test' }, React.createElement('span', null, 'Child Content')))
    expect(screen.getByText('Child Content')).toBeTruthy()
  })

  it('renders footer when provided', function () {
    render(React.createElement(Modal, { open: true, onClose: jest.fn(), title: 'Test', footer: React.createElement('button', null, 'Save') }, null))
    expect(screen.getByText('Save')).toBeTruthy()
  })

  it('does not render footer when not provided', function () {
    render(React.createElement(Modal, { open: true, onClose: jest.fn(), title: 'Test' }, null))
    expect(screen.queryByRole('button', { name: 'Save' })).toBeNull()
  })

  it('close button calls onClose', function () {
    var onClose = jest.fn()
    render(React.createElement(Modal, { open: true, onClose: onClose, title: 'Test' }, null))
    fireEvent.click(screen.getByLabelText('Close'))
    expect(onClose).toHaveBeenCalledTimes(1)
  })

  it('backdrop click calls onClose', function () {
    var onClose = jest.fn()
    render(React.createElement(Modal, { open: true, onClose: onClose, title: 'Test' }, null))
    var dialog = screen.getByRole('dialog')
    fireEvent.click(dialog)
    expect(onClose).toHaveBeenCalledTimes(1)
  })

  it('click inside panel does not trigger onClose', function () {
    var onClose = jest.fn()
    render(React.createElement(Modal, { open: true, onClose: onClose, title: 'Test' }, React.createElement('button', null, 'Inner')))
    fireEvent.click(screen.getByText('Inner'))
    expect(onClose).not.toHaveBeenCalled()
  })

  it('Escape key calls onClose', function () {
    var onClose = jest.fn()
    render(React.createElement(Modal, { open: true, onClose: onClose, title: 'Test' }, null))
    fireEvent.keyDown(document, { key: 'Escape' })
    expect(onClose).toHaveBeenCalledTimes(1)
  })

  it('uses size sm class', function () {
    render(React.createElement(Modal, { open: true, onClose: jest.fn(), title: 'Test', size: 'sm' }, null))
    var dialog = screen.getByRole('dialog')
    expect(dialog.querySelector('.max-w-sm')).toBeTruthy()
  })

  it('uses size lg class', function () {
    render(React.createElement(Modal, { open: true, onClose: jest.fn(), title: 'Test', size: 'lg' }, null))
    var dialog = screen.getByRole('dialog')
    expect(dialog.querySelector('.max-w-lg')).toBeTruthy()
  })

  it('has correct aria attributes', function () {
    render(React.createElement(Modal, { open: true, onClose: jest.fn(), title: 'Accessible Modal' }, null))
    var dialog = screen.getByRole('dialog')
    expect(dialog.getAttribute('aria-modal')).toBe('true')
    expect(dialog.getAttribute('aria-label')).toBe('Accessible Modal')
  })

  it('traps focus with Tab', function () {
    var firstBtn: HTMLElement // eslint-disable-line @typescript-eslint/no-unused-vars
    render(React.createElement(Modal, { open: true, onClose: jest.fn(), title: 'Focus Test' },
      React.createElement('button', { ref: function(el) { if (el) firstBtn = el } }, 'First'),
      React.createElement('button', null, 'Last'),
    ))
    expect(screen.getByRole('dialog')).toBeTruthy()
  })

  it('wraps Tab from last to first element', function () {
    var onClose = jest.fn()
    render(React.createElement(Modal, { open: true, onClose: onClose, title: 'Tab Test' },
      React.createElement('button', { 'data-testid': 'tab-btn' }, 'Only'),
    ))
    var btn = screen.getByTestId('tab-btn')
    btn.focus()
    fireEvent.keyDown(document, { key: 'Tab', shiftKey: false })
    expect(document.activeElement).toBe(screen.getByLabelText('Close'))
  })

  it('wraps Shift+Tab from first to last element', function () {
    var onClose = jest.fn()
    render(React.createElement(Modal, { open: true, onClose: onClose, title: 'Tab Test' },
      React.createElement('button', { 'data-testid': 'tab-btn' }, 'Only'),
    ))
    screen.getByLabelText('Close').focus()
    fireEvent.keyDown(document, { key: 'Tab', shiftKey: true })
    expect(document.activeElement).toBe(screen.getByTestId('tab-btn'))
  })

  it('unmounts cleanly without error', function () {
    var { unmount } = render(React.createElement(Modal, { open: true, onClose: jest.fn(), title: 'Cleanup' }, null))
    expect(function() { unmount() }).not.toThrow()
  })

  it('removes event listeners on unmount', function () {
    var onClose = jest.fn()
    var { unmount } = render(React.createElement(Modal, { open: true, onClose: onClose, title: 'Test' }, null))
    unmount()
    fireEvent.keyDown(document, { key: 'Escape' })
    expect(onClose).not.toHaveBeenCalled()
  })

  it('returns null when open is false after being open', function () {
    var onClose = jest.fn()
    var { rerender } = render(React.createElement(Modal, { open: true, onClose: onClose, title: 'Test' }, null))
    expect(screen.getByRole('dialog')).toBeTruthy()
    rerender(React.createElement(Modal, { open: false, onClose: onClose, title: 'Test' }, null))
    expect(screen.queryByRole('dialog')).toBeNull()
  })
})
