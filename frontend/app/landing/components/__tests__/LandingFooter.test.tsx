jest.mock('next/link', function() { return function({ children, href }) { var React = require('react'); return React.createElement('a', { href: href }, children) } })

var React = require('react')
var { render, screen } = require('@testing-library/react')
var LandingFooter = require('../LandingFooter').default

describe('LandingFooter', function() {
  it('renders brand name', function() {
    render(React.createElement(LandingFooter))
    expect(screen.getByText('SafeVixAI')).toBeTruthy()
  })

  it('renders tagline', function() {
    render(React.createElement(LandingFooter))
    expect(screen.getByText('AI-Powered Road Safety Intelligence')).toBeTruthy()
  })

  it('renders hackathon badge', function() {
    render(React.createElement(LandingFooter))
    expect(screen.getByText('IIT Madras Hackathon 2026')).toBeTruthy()
  })

  it('renders Platform section with links', function() {
    render(React.createElement(LandingFooter))
    expect(screen.getByText('Dashboard')).toBeTruthy()
    expect(screen.getByText('Emergency SOS')).toBeTruthy()
    expect(screen.getByText('Challan Calculator')).toBeTruthy()
    expect(screen.getByText('Hazard Reports')).toBeTruthy()
  })

  it('renders Resources section with links', function() {
    render(React.createElement(LandingFooter))
    expect(screen.getByText('Documentation')).toBeTruthy()
    expect(screen.getByText('GitHub')).toBeTruthy()
    expect(screen.getByText('Dataset Hub')).toBeTruthy()
    expect(screen.getByText('API Reference')).toBeTruthy()
  })

  it('renders Legal section with links', function() {
    render(React.createElement(LandingFooter))
    expect(screen.getByText('Privacy Policy')).toBeTruthy()
    expect(screen.getByText('Terms of Service')).toBeTruthy()
  })

  it('renders copyright', function() {
    render(React.createElement(LandingFooter))
    expect(screen.getByText('© 2026 SafeVixAI. Built for India.')).toBeTruthy()
  })

  it('renders version', function() {
    render(React.createElement(LandingFooter))
    expect(screen.getByText('v2.4.0-SVA')).toBeTruthy()
  })
})
