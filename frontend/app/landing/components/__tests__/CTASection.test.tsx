jest.mock('../../hooks/useLandingGSAP', function() { return { useScrollReveal: function() { return { current: null } } } })

var React = require('react')
var { render, screen: rtlScreen } = require('@testing-library/react')
var CTASection = require('../CTASection').default

describe('CTASection', function() {
  it('renders heading text', function() {
    render(React.createElement(CTASection))
    expect(rtlScreen.getByText('Ready to Transform Road Safety?')).toBeTruthy()
  })

  it('renders GET STARTED badge', function() {
    render(React.createElement(CTASection))
    expect(rtlScreen.getByText('GET STARTED')).toBeTruthy()
  })

  it('renders subtitle', function() {
    render(React.createElement(CTASection))
    expect(rtlScreen.getByText(/Join the intelligence network/)).toBeTruthy()
  })

  it('renders Launch Platform link', function() {
    render(React.createElement(CTASection))
    expect(rtlScreen.getByText('Launch Platform')).toBeTruthy()
  })

  it('renders Explore Intelligence link', function() {
    render(React.createElement(CTASection))
    expect(rtlScreen.getByText('Explore Intelligence')).toBeTruthy()
  })

  it('renders View GitHub link', function() {
    render(React.createElement(CTASection))
    expect(rtlScreen.getByText('View GitHub')).toBeTruthy()
  })
})
