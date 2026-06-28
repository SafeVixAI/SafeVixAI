jest.mock('@gsap/react', function() { return { useGSAP: jest.fn() } })

import { render, screen, fireEvent } from '@testing-library/react'
import React from 'react'
import { Modal } from '../ui/Modal'

describe('Modal', function() {
  it('returns null when not open', function() {
    var c = render(React.createElement(Modal, { open: false, onClose: jest.fn(), title: 'Test' }, null))
    expect(c.container.innerHTML).toBe('')
  })

  it('renders when open', function() {
    render(React.createElement(Modal, { open: true, onClose: jest.fn(), title: 'Test Modal' }, React.createElement('p', null, 'Content')))
    expect(screen.getByRole('dialog')).toBeInTheDocument()
  })

  it('renders title text', function() {
    render(React.createElement(Modal, { open: true, onClose: jest.fn(), title: 'My Title' }, null))
    expect(screen.getByText('My Title')).toBeInTheDocument()
  })

  it('renders children', function() {
    render(React.createElement(Modal, { open: true, onClose: jest.fn(), title: 'Test' }, React.createElement('span', null, 'child content')))
    expect(screen.getByText('child content')).toBeInTheDocument()
  })

  it('renders footer when provided', function() {
    render(React.createElement(Modal, { open: true, onClose: jest.fn(), title: 'Test', footer: React.createElement('button', null, 'Confirm') }, null))
    expect(screen.getByText('Confirm')).toBeInTheDocument()
  })

  it('does not render footer when absent', function() {
    var c = render(React.createElement(Modal, { open: true, onClose: jest.fn(), title: 'Test' }, null))
    var footers = c.container.querySelectorAll('[class*="border-t"]')
    expect(footers.length).toBe(0)
  })

  it('calls onClose when close button clicked', function() {
    var onClose = jest.fn()
    render(React.createElement(Modal, { open: true, onClose: onClose, title: 'Test' }, null))
    fireEvent.click(screen.getByLabelText('Close'))
    expect(onClose).toHaveBeenCalledTimes(1)
  })

  it('calls onClose when backdrop clicked', function() {
    var onClose = jest.fn()
    render(React.createElement(Modal, { open: true, onClose: onClose, title: 'Test' }, null))
    var dialog = screen.getByRole('dialog')
    fireEvent.click(dialog)
    expect(onClose).toHaveBeenCalled()
  })

  it('does not call onClose when panel clicked', function() {
    var onClose = jest.fn()
    var c = render(React.createElement(Modal, { open: true, onClose: onClose, title: 'Test' }, null))
    var panel = c.container.querySelector('[class*="max-w"]')
    if (panel) fireEvent.click(panel)
    expect(onClose).not.toHaveBeenCalled()
  })

  it('calls onClose on Escape key', function() {
    var onClose = jest.fn()
    render(React.createElement(Modal, { open: true, onClose: onClose, title: 'Test' }, null))
    fireEvent.keyDown(document, { key: 'Escape' })
    expect(onClose).toHaveBeenCalled()
  })

  it('renders with sm size classes', function() {
    var c = render(React.createElement(Modal, { open: true, onClose: jest.fn(), title: 'SM', size: 'sm' }, null))
    expect(c.container.querySelector('.max-w-sm')).toBeInTheDocument()
  })

  it('renders with lg size classes', function() {
    var c = render(React.createElement(Modal, { open: true, onClose: jest.fn(), title: 'LG', size: 'lg' }, null))
    expect(c.container.querySelector('.max-w-lg')).toBeInTheDocument()
  })

  it('renders with md size by default', function() {
    var c = render(React.createElement(Modal, { open: true, onClose: jest.fn(), title: 'MD' }, null))
    expect(c.container.querySelector('.max-w-md')).toBeInTheDocument()
  })

  it('sets aria-modal and aria-label on dialog', function() {
    render(React.createElement(Modal, { open: true, onClose: jest.fn(), title: 'Accessible' }, null))
    var dialog = screen.getByRole('dialog')
    expect(dialog.getAttribute('aria-modal')).toBe('true')
    expect(dialog.getAttribute('aria-label')).toBe('Accessible')
  })
})
