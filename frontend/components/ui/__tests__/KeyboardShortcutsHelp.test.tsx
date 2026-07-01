jest.mock('@gsap/react', function() { return { useGSAP: jest.fn() } })
jest.mock('@/lib/gsap', function() { return { gsap: { fromTo: jest.fn() } } })

var React = require('react')
var { render, screen, fireEvent } = require('@testing-library/react')
var { KeyboardShortcutsHelp } = require('../KeyboardShortcutsHelp')

describe('KeyboardShortcutsHelp', function() {
  beforeEach(function() {
    jest.useFakeTimers()
  })

  afterEach(function() {
    jest.useRealTimers()
  })

  it('returns null when closed', function() {
    var { container } = render(React.createElement(KeyboardShortcutsHelp))
    expect(container.innerHTML).toBe('')
  })

  it('opens when ? key is pressed', function() {
    render(React.createElement(KeyboardShortcutsHelp))
    fireEvent.keyDown(document, { key: '?' })
    expect(screen.getByText('Keyboard Shortcuts')).toBeTruthy()
  })

  it('renders all default shortcuts', function() {
    render(React.createElement(KeyboardShortcutsHelp))
    fireEvent.keyDown(document, { key: '?' })
    expect(screen.getByText('Open command palette')).toBeTruthy()
    expect(screen.getByText('Toggle keyboard shortcuts')).toBeTruthy()
    expect(screen.getByText('Pan map')).toBeTruthy()
    expect(screen.getByText('Zoom map in/out')).toBeTruthy()
    expect(screen.getByText('Close dialogs / Cancel SOS')).toBeTruthy()
    expect(screen.getByText('Send chat message / Confirm action')).toBeTruthy()
  })

  it('shows key bindings for each shortcut', function() {
    render(React.createElement(KeyboardShortcutsHelp))
    fireEvent.keyDown(document, { key: '?' })
    expect(screen.getByText('Cmd+K')).toBeTruthy()
    expect(screen.getByText('Esc')).toBeTruthy()
    expect(screen.getByText('Enter')).toBeTruthy()
  })

  it('closes on Escape key', function() {
    render(React.createElement(KeyboardShortcutsHelp))
    fireEvent.keyDown(document, { key: '?' })
    expect(screen.getByText('Keyboard Shortcuts')).toBeTruthy()
    fireEvent.keyDown(document, { key: 'Escape' })
    expect(screen.queryByText('Keyboard Shortcuts')).toBeNull()
  })

  it('closes on overlay click', function() {
    render(React.createElement(KeyboardShortcutsHelp))
    fireEvent.keyDown(document, { key: '?' })
    expect(screen.getByText('Keyboard Shortcuts')).toBeTruthy()
    var overlay = document.querySelector('[role="dialog"]')
    fireEvent.click(overlay)
    expect(screen.queryByText('Keyboard Shortcuts')).toBeNull()
  })

  it('does not open when ? is pressed in an input', function() {
    render(React.createElement('div', null,
      React.createElement('input', { 'data-testid': 'input' }),
      React.createElement(KeyboardShortcutsHelp)
    ))
    var input = document.querySelector('input')
    fireEvent.keyDown(input, { key: '?' })
    expect(screen.queryByText('Keyboard Shortcuts')).toBeNull()
  })

  it('does not trigger on Ctrl+?', function() {
    render(React.createElement(KeyboardShortcutsHelp))
    fireEvent.keyDown(document, { key: '?', ctrlKey: true })
    expect(screen.queryByText('Keyboard Shortcuts')).toBeNull()
  })

  it('shows close hint text at bottom', function() {
    render(React.createElement(KeyboardShortcutsHelp))
    fireEvent.keyDown(document, { key: '?' })
    expect(screen.getByText(/Press \? or Esc to close/)).toBeTruthy()
  })
})
