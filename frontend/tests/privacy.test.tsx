jest.mock('next/navigation', function() { return { useRouter: function() { return { push: jest.fn(), back: jest.fn() } }, useSearchParams: function() { return new URLSearchParams() } } })
jest.mock('@/components/ui/SurfaceCard', function() { return { SurfaceCard: function({ children, ...rest }) { return rest.className ? require('react').createElement('div', { 'data-testid': 'surface-card', className: rest.className }, children) : children } } })
jest.mock('@/components/dashboard/SystemHeader', function() { return function() { return null } })
jest.mock('lucide-react', function() { return new Proxy({}, { get: function() { return function() { return null } } }) })

var React = require('react')
var { render, screen: rtlScreen } = require('@testing-library/react')
var Page = require('../app/privacy/page').default

describe('PrivacyPolicyPage', function() {
  it('renders Privacy Policy heading', function() {
    render(React.createElement(Page))
    expect(rtlScreen.getByText('Privacy Policy')).toBeTruthy()
  })

  it('renders back to settings button', function() {
    render(React.createElement(Page))
    expect(rtlScreen.getByText('Back to Settings')).toBeTruthy()
  })

  it('renders DPDP Act badge text', function() {
    render(React.createElement(Page))
    expect(rtlScreen.getAllByText(/DPDP Act 2023/).length).toBeGreaterThanOrEqual(1)
  })

  it('renders Information We Collect section heading', function() {
    render(React.createElement(Page))
    expect(rtlScreen.getByText(/Information We Collect/)).toBeTruthy()
  })

  it('renders effective date', function() {
    render(React.createElement(Page))
    expect(rtlScreen.getByText(/Effective Date/)).toBeTruthy()
  })

  it('renders DPDP Act 2023 Compliance section', function() {
    render(React.createElement(Page))
    expect(rtlScreen.getByText(/DPDP Act 2023 Compliance/)).toBeTruthy()
  })

  it('renders Right to Erasure section', function() {
    render(React.createElement(Page))
    expect(rtlScreen.getByText(/Right to Erasure/)).toBeTruthy()
  })

  it('renders AI Vector & LLM Privacy section', function() {
    render(React.createElement(Page))
    expect(rtlScreen.getByText(/AI Vector/)).toBeTruthy()
  })

  it('renders Data Protection Officer contact', function() {
    render(React.createElement(Page))
    expect(rtlScreen.getAllByText(/Data Protection Officer/).length).toBeGreaterThanOrEqual(1)
  })

  it('renders DPO email address', function() {
    render(React.createElement(Page))
    expect(rtlScreen.getAllByText(/dpo@safevixai.gov.in/).length).toBeGreaterThanOrEqual(1)
  })
})
