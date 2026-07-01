jest.mock('next/navigation', function() { return { useRouter: function() { return { push: jest.fn(), back: jest.fn() } }, useSearchParams: function() { return new URLSearchParams() } } })
jest.mock('@/components/ui/SurfaceCard', function() { return { SurfaceCard: function({ children, ...rest }) { return rest.className ? require('react').createElement('div', { 'data-testid': 'surface-card', className: rest.className }, children) : children } } })
jest.mock('@/components/dashboard/SystemHeader', function() { return function() { return null } })
jest.mock('lucide-react', function() { return new Proxy({}, { get: function() { return function() { return null } } }) })

var React = require('react')
var { render, screen } = require('@testing-library/react')
var Page = require('../app/privacy/page').default

describe('PrivacyPolicyPage', function() {
  it('renders Privacy Policy heading', function() {
    render(React.createElement(Page))
    expect(screen.getByText('Privacy Policy')).toBeTruthy()
  })

  it('renders back to settings button', function() {
    render(React.createElement(Page))
    expect(screen.getByText('Back to Settings')).toBeTruthy()
  })

  it('renders DPDP Act badge text', function() {
    render(React.createElement(Page))
    expect(screen.getAllByText(/DPDP Act 2023/).length).toBeGreaterThanOrEqual(1)
  })

  it('renders Information We Collect section heading', function() {
    render(React.createElement(Page))
    expect(screen.getByText(/Information We Collect/)).toBeTruthy()
  })

  it('renders effective date', function() {
    render(React.createElement(Page))
    expect(screen.getByText(/Effective Date/)).toBeTruthy()
  })
})
