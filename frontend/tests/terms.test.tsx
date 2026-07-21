jest.mock('next/navigation', function() { return { useRouter: function() { return { push: jest.fn(), back: jest.fn() } }, useSearchParams: function() { return new URLSearchParams() } } })
jest.mock('@/components/ui/SurfaceCard', function() { return { SurfaceCard: function({ children, ...rest }) { return rest.className ? require('react').createElement('div', { 'data-testid': 'surface-card', className: rest.className }, children) : children } } })
jest.mock('@/components/dashboard/SystemHeader', function() { return function() { return null } })
jest.mock('lucide-react', function() { return new Proxy({}, { get: function() { return function() { return null } } }) })

var React = require('react')
var { render, screen: rtlScreen } = require('@testing-library/react')
var Page = require('../app/terms/page').default

describe('TermsOfServicePage', function() {
  it('renders Terms of Service heading', function() {
    render(React.createElement(Page))
    expect(rtlScreen.getByText('Terms of Service')).toBeTruthy()
  })

  it('renders back to settings button', function() {
    render(React.createElement(Page))
    expect(rtlScreen.getByText('Back to Settings')).toBeTruthy()
  })

  it('renders Citizen SLA badge text', function() {
    render(React.createElement(Page))
    expect(rtlScreen.getByText(/Citizen SLA/)).toBeTruthy()
  })

  it('renders Scope & Acceptable Use section heading', function() {
    render(React.createElement(Page))
    expect(rtlScreen.getByText(/Scope & Acceptable Use/)).toBeTruthy()
  })

  it('renders effective date', function() {
    render(React.createElement(Page))
    expect(rtlScreen.getByText(/Effective Date/)).toBeTruthy()
  })

  it('renders SLA & Emergency Disclaimer section', function() {
    render(React.createElement(Page))
    expect(rtlScreen.getByText(/SLA & Emergency Disclaimer/)).toBeTruthy()
  })

  it('renders critical warning for emergencies', function() {
    render(React.createElement(Page))
    expect(rtlScreen.getByText(/CRITICAL WARNING FOR EMERGENCIES/)).toBeTruthy()
  })

  it('renders Challan Calculator Disclaimer section', function() {
    render(React.createElement(Page))
    expect(rtlScreen.getByText(/Challan Calculator Disclaimer/)).toBeTruthy()
  })

  it('renders Limit of Liability section', function() {
    render(React.createElement(Page))
    expect(rtlScreen.getByText(/Limit of Liability/)).toBeTruthy()
  })

  it('renders Governing Law section', function() {
    render(React.createElement(Page))
    expect(rtlScreen.getByText(/Governing Law/)).toBeTruthy()
  })

  it('renders emergency number 112 in disclaimer', function() {
    render(React.createElement(Page))
    expect(rtlScreen.getByText(/112/)).toBeTruthy()
  })
})
