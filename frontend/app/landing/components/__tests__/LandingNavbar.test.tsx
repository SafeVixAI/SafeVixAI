jest.mock('@gsap/react', function() { return { useGSAP: jest.fn() } })
jest.mock('@/lib/gsap', function() { return { gsap: { fromTo: jest.fn() } } })
jest.mock('next/link', function() { return function({ children, href, ...rest }) { const React = require('react'); return React.createElement('a', { href: href, 'aria-label': rest['aria-label'] }, children) } })
jest.mock('lucide-react', function() { return { Menu: function() { return null }, X: function() { return null } } })

const React = require('react')
const { render, screen: rtlScreen } = require('@testing-library/react')
const LandingNavbar = require('../LandingNavbar').default

describe('LandingNavbar', function() {
  it('renders brand name', function() {
    render(React.createElement(LandingNavbar))
    expect(rtlScreen.getByText('SafeVixAI')).toBeTruthy()
  })

  it('renders nav links', function() {
    render(React.createElement(LandingNavbar))
    expect(rtlScreen.getAllByText('Platform').length).toBeGreaterThanOrEqual(1)
    expect(rtlScreen.getAllByText('Modules').length).toBeGreaterThanOrEqual(1)
    expect(rtlScreen.getAllByText('Intelligence').length).toBeGreaterThanOrEqual(1)
    expect(rtlScreen.getAllByText('Mission').length).toBeGreaterThanOrEqual(1)
  })

  it('renders Launch Platform links', function() {
    render(React.createElement(LandingNavbar))
    expect(rtlScreen.getAllByText('Launch Platform').length).toBeGreaterThanOrEqual(1)
  })

  it('has navigation elements', function() {
    render(React.createElement(LandingNavbar))
    const navs = rtlScreen.getAllByRole('navigation')
    expect(navs.length).toBeGreaterThanOrEqual(1)
  })

  it('has mobile menu button', function() {
    render(React.createElement(LandingNavbar))
    expect(rtlScreen.getByLabelText('Open menu')).toBeTruthy()
  })
})
