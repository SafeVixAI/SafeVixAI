jest.mock('@gsap/react', function() { return { useGSAP: jest.fn() } })
jest.mock('@/lib/gsap', function() { return { gsap: { fromTo: jest.fn() } } })
jest.mock('next/link', function() { return function({ children, href, ...rest }) { var React = require('react'); return React.createElement('a', { href: href, 'aria-label': rest['aria-label'] }, children) } })
jest.mock('lucide-react', function() { return { Menu: function() { return null }, X: function() { return null } } })

var React = require('react')
var { render, screen, fireEvent } = require('@testing-library/react')
var LandingNavbar = require('../LandingNavbar').default

describe('LandingNavbar', function() {
  it('renders brand name', function() {
    render(React.createElement(LandingNavbar))
    expect(screen.getByText('SafeVixAI')).toBeTruthy()
  })

  it('renders nav links', function() {
    render(React.createElement(LandingNavbar))
    expect(screen.getAllByText('Platform').length).toBeGreaterThanOrEqual(1)
    expect(screen.getAllByText('Modules').length).toBeGreaterThanOrEqual(1)
    expect(screen.getAllByText('Intelligence').length).toBeGreaterThanOrEqual(1)
    expect(screen.getAllByText('Mission').length).toBeGreaterThanOrEqual(1)
  })

  it('renders Launch Platform links', function() {
    render(React.createElement(LandingNavbar))
    expect(screen.getAllByText('Launch Platform').length).toBeGreaterThanOrEqual(1)
  })

  it('has navigation elements', function() {
    render(React.createElement(LandingNavbar))
    var navs = screen.getAllByRole('navigation')
    expect(navs.length).toBeGreaterThanOrEqual(1)
  })

  it('has mobile menu button', function() {
    render(React.createElement(LandingNavbar))
    expect(screen.getByLabelText('Open menu')).toBeTruthy()
  })
})
