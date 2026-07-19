jest.mock('@gsap/react', function() { return { useGSAP: jest.fn() } })
jest.mock('@/lib/gsap', function() { return { gsap: { fromTo: jest.fn() } } })

var React = require('react')
var { render, screen: rtlScreen, fireEvent } = require('@testing-library/react')
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
    expect(rtlScreen.getByText('Keyboard Shortcuts')).toBeTruthy()
  })

  it('renders all default shortcuts', function() {
    render(React.createElement(KeyboardShortcutsHelp))
    fireEvent.keyDown(document, { key: '?' })
    expect(rtlScreen.getByText('Open command palette')).toBeTruthy()
    expect(rtlScreen.getByText('Toggle keyboard shortcuts')).toBeTruthy()
    expect(rtlScreen.getByText('Pan map')).toBeTruthy()
    expect(rtlScreen.getByText('Zoom map in/out')).toBeTruthy()
    expect(rtlScreen.getByText('Close dialogs / Cancel SOS')).toBeTruthy()
    expect(rtlScreen.getByText('Send chat message / Confirm action')).toBeTruthy()
  })

  it('shows key bindings for each shortcut', function() {
    render(React.createElement(KeyboardShortcutsHelp))
    fireEvent.keyDown(document, { key: '?' })
    expect(rtlScreen.getByText('Cmd+K')).toBeTruthy()
    expect(rtlScreen.getByText('Esc')).toBeTruthy()
    expect(rtlScreen.getByText('Enter')).toBeTruthy()
  })

  it('closes on Escape key', function() {
    render(React.createElement(KeyboardShortcutsHelp))
    fireEvent.keyDown(document, { key: '?' })
    expect(rtlScreen.getByText('Keyboard Shortcuts')).toBeTruthy()
    fireEvent.keyDown(document, { key: 'Escape' })
    expect(rtlScreen.queryByText('Keyboard Shortcuts')).toBeNull()
  })

  it('closes on overlay click', function() {
    render(React.createElement(KeyboardShortcutsHelp))
    fireEvent.keyDown(document, { key: '?' })
    expect(rtlScreen.getByText('Keyboard Shortcuts')).toBeTruthy()
    var overlay = document.querySelector('[role="dialog"]')
    fireEvent.click(overlay)
    expect(rtlScreen.queryByText('Keyboard Shortcuts')).toBeNull()
  })

  it('does not open when ? is pressed in an input', function() {
    render(React.createElement('div', null,
      React.createElement('input', { 'data-testid': 'input' }),
      React.createElement(KeyboardShortcutsHelp)
    ))
    var input = document.querySelector('input')
    fireEvent.keyDown(input, { key: '?' })
    expect(rtlScreen.queryByText('Keyboard Shortcuts')).toBeNull()
  })

  it('does not trigger on Ctrl+?', function() {
    render(React.createElement(KeyboardShortcutsHelp))
    fireEvent.keyDown(document, { key: '?', ctrlKey: true })
    expect(rtlScreen.queryByText('Keyboard Shortcuts')).toBeNull()
  })

  it('shows close hint text at bottom', function() {
    render(React.createElement(KeyboardShortcutsHelp))
    fireEvent.keyDown(document, { key: '?' })
    expect(rtlScreen.getByText(/Press \? or Esc to close/)).toBeTruthy()
  })
})
