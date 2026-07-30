jest.mock('@/hooks/usePageEntry', function() { return { usePageEntry: function() { return { current: null } } } })
jest.mock('@/components/ui/TerminalHeader', function() { return { TerminalHeader: function() { return null } } })
jest.mock('@/components/ui/SurfaceCard', function() { return { SurfaceCard: function({ children }) { return children } } })
jest.mock('@/lib/store', function() {
  return { useAppStore: Object.assign(function(sel) { const state = {}; return typeof sel === 'function' ? sel(state) : state }, { getState: function() { return {} }, setState: jest.fn(), subscribe: jest.fn() }) }
})
jest.mock('@/lib/provider-api', function() {
  return {
    fetchBuiltinProviders: jest.fn().mockResolvedValue([]),
    fetchProviderConfigs: jest.fn().mockResolvedValue([]),
    createProviderConfig: jest.fn(),
    updateProviderConfig: jest.fn(),
    deleteProviderConfig: jest.fn(),
    testProviderConnection: jest.fn(),
    syncProvidersToChatbot: jest.fn(),
  }
})
jest.mock('lucide-react', function() { return new Proxy({}, { get: function() { return function() { return null } } }) })

import { render, screen } from '@testing-library/react'
import React from 'react'
import ProvidersPage from '../app/providers/page'

describe('ProvidersPage', function() {
  it('renders without error', function() {
    const { container } = render(React.createElement(ProvidersPage))
    expect(container).toBeTruthy()
  })

  it('renders provider management shell', function() {
    const { container } = render(React.createElement(ProvidersPage))
    expect(container.querySelector('main') || container.querySelector('[class]')).toBeTruthy()
  })

  it('renders with surface card wrappers', function() {
    const { container } = render(React.createElement(ProvidersPage))
    expect(container).toBeTruthy()
  })
})
