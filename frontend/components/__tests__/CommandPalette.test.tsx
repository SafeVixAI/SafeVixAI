jest.mock('@/lib/gsap', function() {
  return { gsap: { fromTo: jest.fn(function() { return {} }), to: jest.fn() } }
})
jest.mock('@gsap/react', function() {
  const React2 = require('react');
  return {
    useGSAP: function(cb: any, opts?: any) {
      React2.useEffect(function() {
        if (typeof cb === 'function') cb();
      }, opts?.dependencies || []);
    },
  };
})
jest.mock('cmdk', function() {
  const React = require('react')
  function FakeInput() { return null }
  function FakeList(props: any) { return React.createElement('div', null, props.children) }
  function FakeEmpty() { return null }
  function FakeGroup(props: any) { return React.createElement('div', null, props.children) }
  function FakeItem(props: any) { return React.createElement('div', { onClick: props.onSelect }, props.children) }
  function FakeRoot(props: any) {
    return React.createElement('div', { 'data-testid': 'cmdk-root', role: 'dialog', 'aria-modal': 'true', 'aria-label': 'Search commands' }, props.children)
  }
  FakeRoot.Input = FakeInput
  FakeRoot.List = FakeList
  FakeRoot.Empty = FakeEmpty
  FakeRoot.Group = FakeGroup
  FakeRoot.Item = FakeItem
  return { Command: FakeRoot, Input: FakeInput, List: FakeList, Empty: FakeEmpty, Group: FakeGroup, Item: FakeItem }
})
const mockPush = jest.fn()
jest.mock('next/navigation', function() {
  return { useRouter: function() { return { push: mockPush } }, usePathname: function() { return '/' }, useSearchParams: function() { return new URLSearchParams() } }
})

import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import React from 'react'
import { CommandPalette } from '../search/CommandPalette'

describe('CommandPalette', function() {
  let map: Record<string, Function> = {}
  const originalAddEventListener = document.addEventListener.bind(document)
  const originalRemoveEventListener = document.removeEventListener.bind(document)

  beforeEach(function() {
    jest.clearAllMocks()
    map = {}
    document.addEventListener = jest.fn(function(event: string, cb: any) { map[event] = cb })
    document.removeEventListener = jest.fn(function(event: string) { delete map[event] })
  })

  afterEach(function() {
    document.addEventListener = originalAddEventListener
    document.removeEventListener = originalRemoveEventListener
  })

  it('returns null when not open', function() {
    const c = render(React.createElement(CommandPalette))
    expect(c.container.innerHTML).toBe('')
  })

  it('registers keydown listener on mount', function() {
    render(React.createElement(CommandPalette))
    expect(document.addEventListener).toHaveBeenCalledWith('keydown', expect.any(Function))
  })

  it('opens on Cmd+K keypress', async function() {
    render(React.createElement(CommandPalette))
    const keydown = map['keydown']
    if (keydown) keydown({ key: 'k', metaKey: true, preventDefault: jest.fn() })
    await waitFor(function() { expect(screen.getByTestId('cmdk-root')).toBeInTheDocument() })
  })

  it('opens on Ctrl+K keypress', async function() {
    render(React.createElement(CommandPalette))
    const keydown = map['keydown']
    if (keydown) keydown({ key: 'k', ctrlKey: true, preventDefault: jest.fn() })
    await waitFor(function() { expect(screen.getByTestId('cmdk-root')).toBeInTheDocument() })
  })

  it('toggles closed on second Cmd+K', async function() {
    render(React.createElement(CommandPalette))
    const keydown = map['keydown']
    if (keydown) keydown({ key: 'k', metaKey: true, preventDefault: jest.fn() })
    await waitFor(function() { expect(screen.getByTestId('cmdk-root')).toBeInTheDocument() })
    if (keydown) keydown({ key: 'k', metaKey: true, preventDefault: jest.fn() })
    await waitFor(function() { expect(screen.queryByTestId('cmdk-root')).not.toBeInTheDocument() })
  })

  it('closes when clicking overlay', async function() {
    render(React.createElement(CommandPalette))
    const keydown = map['keydown']
    if (keydown) keydown({ key: 'k', metaKey: true, preventDefault: jest.fn() })
    await waitFor(function() { expect(screen.getByTestId('cmdk-root')).toBeInTheDocument() })
    const overlay = document.querySelector('[class*="fixed"]')
    if (overlay) fireEvent.click(overlay)
    expect(screen.queryByTestId('cmdk-root')).not.toBeInTheDocument()
  })

  it('removes keydown listener on unmount', function() {
    const c = render(React.createElement(CommandPalette))
    c.unmount()
    expect(document.removeEventListener).toHaveBeenCalledWith('keydown', expect.any(Function))
  })

  it('renders navigation items when open', async function() {
    render(React.createElement(CommandPalette))
    const keydown = map['keydown']
    if (keydown) keydown({ key: 'k', metaKey: true, preventDefault: jest.fn() })
    await waitFor(function() { expect(screen.getByText('Find nearest hospital')).toBeInTheDocument() })
    expect(screen.getByText('Activate Emergency SOS')).toBeInTheDocument()
    expect(screen.getByText('First Aid Guide')).toBeInTheDocument()
    expect(screen.getByText('Calculate Traffic Fine')).toBeInTheDocument()
    expect(screen.getByText('Report Road Issue')).toBeInTheDocument()
    expect(screen.getByText('AI Assistant')).toBeInTheDocument()
  })

  it('navigates to locator on Find nearest hospital click', async function() {
    render(React.createElement(CommandPalette))
    const keydown = map['keydown']
    if (keydown) keydown({ key: 'k', metaKey: true, preventDefault: jest.fn() })
    await waitFor(function() { expect(screen.getByText('Find nearest hospital')).toBeInTheDocument() })
    fireEvent.click(screen.getByText('Find nearest hospital'))
    expect(mockPush).toHaveBeenCalledWith('/locator')
  })

  it('navigates to first-aid on First Aid Guide click', async function() {
    render(React.createElement(CommandPalette))
    const keydown = map['keydown']
    if (keydown) keydown({ key: 'k', metaKey: true, preventDefault: jest.fn() })
    await waitFor(function() { expect(screen.getByText('First Aid Guide')).toBeInTheDocument() })
    fireEvent.click(screen.getByText('First Aid Guide'))
    expect(mockPush).toHaveBeenCalledWith('/first-aid')
  })

  it('navigates to challan on Calculate Traffic Fine click', async function() {
    render(React.createElement(CommandPalette))
    const keydown = map['keydown']
    if (keydown) keydown({ key: 'k', metaKey: true, preventDefault: jest.fn() })
    await waitFor(function() { expect(screen.getByText('Calculate Traffic Fine')).toBeInTheDocument() })
    fireEvent.click(screen.getByText('Calculate Traffic Fine'))
    expect(mockPush).toHaveBeenCalledWith('/challan')
  })

  it('navigates to report on Report Road Issue click', async function() {
    render(React.createElement(CommandPalette))
    const keydown = map['keydown']
    if (keydown) keydown({ key: 'k', metaKey: true, preventDefault: jest.fn() })
    await waitFor(function() { expect(screen.getByText('Report Road Issue')).toBeInTheDocument() })
    fireEvent.click(screen.getByText('Report Road Issue'))
    expect(mockPush).toHaveBeenCalledWith('/report')
  })

  it('navigates to assistant on AI Assistant click', async function() {
    render(React.createElement(CommandPalette))
    const keydown = map['keydown']
    if (keydown) keydown({ key: 'k', metaKey: true, preventDefault: jest.fn() })
    await waitFor(function() { expect(screen.getByText('AI Assistant')).toBeInTheDocument() })
    fireEvent.click(screen.getByText('AI Assistant'))
    expect(mockPush).toHaveBeenCalledWith('/assistant')
  })
})
