jest.mock('@/lib/store', function() { return {
  useAppStore: function(selector) {
    const state = {
      gpsLocation: { lat: 13.0827, lon: 80.2707 },
      connectivity: 'online',
      isAuthenticated: false,
      userProfile: { name: 'Test', displayId: 'TST001' },
    }
    return selector ? selector(state) : state
  },
} })

jest.mock('next/navigation', function() { return {
  useRouter: function() { return { push: jest.fn(), back: jest.fn(), replace: jest.fn() } },
  useSearchParams: function() { return new URLSearchParams() },
  usePathname: function() { return '/' },
} })

const React = require('react')
const { render } = require('@testing-library/react')
const { axe, toHaveNoViolations } = require('jest-axe')

expect.extend(toHaveNoViolations)

describe('Accessibility Compliance - Components', function() {
  it('SurfaceCard has no axe violations', async function() {
    const mod = require('@/components/ui/SurfaceCard')
    const { container } = render(React.createElement(mod.SurfaceCard, { variant: 'standard', padding: 'md' }, React.createElement('p', null, 'Card content')))
    const results = await axe(container)
    expect(results).toHaveNoViolations()
  })

  it('Modal has no axe violations', async function() {
    const mod = require('@/components/ui/Modal')
    const { container } = render(React.createElement(mod.Modal, { isOpen: true, onClose: jest.fn(), title: 'Test Modal' }, React.createElement('p', null, 'Modal content')))
    const results = await axe(container)
    expect(results).toHaveNoViolations()
  })

  it('SkeletonCard has no axe violations', async function() {
    const mod = require('@/components/ui/SkeletonCard')
    const { container } = render(React.createElement(mod.SkeletonCard))
    const results = await axe(container)
    expect(results).toHaveNoViolations()
  })

  it('Login page has no axe violations', async function() {
    const mod = require('@/app/login/page')
    const { container } = render(React.createElement(mod.default))
    const results = await axe(container)
    expect(results).toHaveNoViolations()
  })
})
