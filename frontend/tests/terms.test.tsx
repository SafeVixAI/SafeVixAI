jest.mock('next/navigation', function() { return { useRouter: function() { return { push: jest.fn(), back: jest.fn() } }, useSearchParams: function() { return new URLSearchParams() } } })
jest.mock('@/components/ui/SurfaceCard', function() { return { SurfaceCard: function({ children, ...rest }) { return rest.className ? require('react').createElement('div', { 'data-testid': 'surface-card', className: rest.className }, children) : children } } })
jest.mock('@/components/dashboard/SystemHeader', function() { return function() { return null } })
jest.mock('lucide-react', function() { return new Proxy({}, { get: function() { return function() { return null } } }) })

var React = require('react')
var { render, screen } = require('@testing-library/react')
var Page = require('../app/terms/page').default

describe('TermsOfServicePage', function() {
  it('renders Terms of Service heading', function() {
    render(React.createElement(Page))
    expect(screen.getByText('Terms of Service')).toBeTruthy()
  })

  it('renders back to settings button', function() {
    render(React.createElement(Page))
    expect(screen.getByText('Back to Settings')).toBeTruthy()
  })

  it('renders Citizen SLA badge text', function() {
    render(React.createElement(Page))
    expect(screen.getByText(/Citizen SLA/)).toBeTruthy()
  })

  it('renders Scope section heading', function() {
    render(React.createElement(Page))
    expect(screen.getByText(/Scope & Acceptable Use/)).toBeTruthy()
  })

  it('renders effective date', function() {
    render(React.createElement(Page))
    expect(screen.getByText(/Effective Date/)).toBeTruthy()
  })
})
