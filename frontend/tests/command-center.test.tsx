jest.mock('@/components/ui/TerminalHeader', function() { return { TerminalHeader: function() { return null } } })
jest.mock('@/components/ui/SurfaceCard', function() { return { SurfaceCard: function({ children }) { return children } } })
jest.mock('@/lib/api', function() { return { client: { get: jest.fn().mockResolvedValue({ data: {} }), post: jest.fn().mockResolvedValue({ data: {} }) } } })
jest.mock('@/lib/sounds', function() { return { sounds: { play: jest.fn(), sev5Alert: jest.fn() } } })
jest.mock('next/dynamic', function() { return function() { return function() { return null } } })
jest.mock('lucide-react', function() { return new Proxy({}, { get: function() { return function() { return null } } }) })

import { render, screen } from '@testing-library/react'
import React from 'react'
import CommandCenterPage from '../app/command-center/page'

describe('CommandCenterPage', function() {
  it('renders Command Center heading', function() {
    render(React.createElement(CommandCenterPage))
    expect(screen.getByText('Command Center')).toBeTruthy()
  })

  it('renders outer container structure', function() {
    var { container } = render(React.createElement(CommandCenterPage))
    expect(container).toBeTruthy()
    expect(container.querySelector('div[class]')).toBeTruthy()
  })

  it('renders surface card wrapper with content', function() {
    var { container } = render(React.createElement(CommandCenterPage))
    expect(container.textContent).toBeTruthy()
  })

  it('renders page structure', function() {
    var { container } = render(React.createElement(CommandCenterPage))
    expect(container.textContent).toContain('Command Center')
  })

  it('renders without crashing', function() {
    var { container } = render(React.createElement(CommandCenterPage))
    expect(container.querySelector('div')).toBeTruthy()
  })
})
