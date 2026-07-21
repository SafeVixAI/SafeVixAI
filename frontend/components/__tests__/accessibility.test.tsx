jest.mock('@/lib/store', function() { return {
  useAppStore: function(selector) {
    var state = {
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

var React = require('react')
var { render } = require('@testing-library/react')
var { axe, toHaveNoViolations } = require('jest-axe')

expect.extend(toHaveNoViolations)

describe('Accessibility Compliance - Components', function() {
  it('SurfaceCard has no axe violations', async function() {
    var mod = require('@/components/ui/SurfaceCard')
    var { container } = render(React.createElement(mod.SurfaceCard, { variant: 'standard', padding: 'md' }, React.createElement('p', null, 'Card content')))
    var results = await axe(container)
    expect(results).toHaveNoViolations()
  })

  it('Modal has no axe violations', async function() {
    var mod = require('@/components/ui/Modal')
    var { container } = render(React.createElement(mod.Modal, { isOpen: true, onClose: jest.fn(), title: 'Test Modal' }, React.createElement('p', null, 'Modal content')))
    var results = await axe(container)
    expect(results).toHaveNoViolations()
  })

  it('SkeletonCard has no axe violations', async function() {
    var mod = require('@/components/ui/SkeletonCard')
    var { container } = render(React.createElement(mod.SkeletonCard))
    var results = await axe(container)
    expect(results).toHaveNoViolations()
  })

  it('Login page has no axe violations', async function() {
    var mod = require('@/app/login/page')
    var { container } = render(React.createElement(mod.default))
    var results = await axe(container)
    expect(results).toHaveNoViolations()
  })
})
