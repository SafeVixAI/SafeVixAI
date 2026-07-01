jest.mock('../../hooks/useLandingGSAP', function() { return { useScrollReveal: function() { return { current: null } } } })

var React = require('react')
var { render, screen } = require('@testing-library/react')
var CTASection = require('../CTASection').default

describe('CTASection', function() {
  it('renders heading text', function() {
    render(React.createElement(CTASection))
    expect(screen.getByText('Ready to Transform Road Safety?')).toBeTruthy()
  })

  it('renders GET STARTED badge', function() {
    render(React.createElement(CTASection))
    expect(screen.getByText('GET STARTED')).toBeTruthy()
  })

  it('renders subtitle', function() {
    render(React.createElement(CTASection))
    expect(screen.getByText(/Join the intelligence network/)).toBeTruthy()
  })

  it('renders Launch Platform link', function() {
    render(React.createElement(CTASection))
    expect(screen.getByText('Launch Platform')).toBeTruthy()
  })

  it('renders Explore Intelligence link', function() {
    render(React.createElement(CTASection))
    expect(screen.getByText('Explore Intelligence')).toBeTruthy()
  })

  it('renders View GitHub link', function() {
    render(React.createElement(CTASection))
    expect(screen.getByText('View GitHub')).toBeTruthy()
  })
})
