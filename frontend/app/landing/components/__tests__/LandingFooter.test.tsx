jest.mock('next/link', function() { return function({ children, href }) { var React = require('react'); return React.createElement('a', { href: href }, children) } })

var React = require('react')
var { render, screen: rtlScreen } = require('@testing-library/react')
var LandingFooter = require('../LandingFooter').default

describe('LandingFooter', function() {
  it('renders brand name', function() {
    render(React.createElement(LandingFooter))
    expect(rtlScreen.getByText('SafeVixAI')).toBeTruthy()
  })

  it('renders tagline', function() {
    render(React.createElement(LandingFooter))
    expect(rtlScreen.getByText('AI-Powered Road Safety Intelligence')).toBeTruthy()
  })

  it('renders hackathon badge', function() {
    render(React.createElement(LandingFooter))
    expect(rtlScreen.getByText('IIT Madras Hackathon 2026')).toBeTruthy()
  })

  it('renders Platform section with links', function() {
    render(React.createElement(LandingFooter))
    expect(rtlScreen.getByText('Dashboard')).toBeTruthy()
    expect(rtlScreen.getByText('Emergency SOS')).toBeTruthy()
    expect(rtlScreen.getByText('Challan Calculator')).toBeTruthy()
    expect(rtlScreen.getByText('Hazard Reports')).toBeTruthy()
  })

  it('renders Resources section with links', function() {
    render(React.createElement(LandingFooter))
    expect(rtlScreen.getByText('Documentation')).toBeTruthy()
    expect(rtlScreen.getByText('GitHub')).toBeTruthy()
    expect(rtlScreen.getByText('Dataset Hub')).toBeTruthy()
    expect(rtlScreen.getByText('API Reference')).toBeTruthy()
  })

  it('renders Legal section with links', function() {
    render(React.createElement(LandingFooter))
    expect(rtlScreen.getByText('Privacy Policy')).toBeTruthy()
    expect(rtlScreen.getByText('Terms of Service')).toBeTruthy()
  })

  it('renders copyright', function() {
    render(React.createElement(LandingFooter))
    expect(rtlScreen.getByText('© 2026 SafeVixAI. Built for India.')).toBeTruthy()
  })

  it('renders version', function() {
    render(React.createElement(LandingFooter))
    expect(rtlScreen.getByText('v2.4.0-SVA')).toBeTruthy()
  })
})
