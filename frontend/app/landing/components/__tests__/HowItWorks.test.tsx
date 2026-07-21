jest.mock('@gsap/react', function() { return { useGSAP: jest.fn() } })
jest.mock('@/lib/gsap', function() { return { gsap: { fromTo: jest.fn(), to: jest.fn(), set: jest.fn(), timeline: function() { return { fromTo: jest.fn(), to: jest.fn(), kill: jest.fn() } } } } })
jest.mock('../../hooks/useLandingGSAP', function() {
  var React = require('react')
  return {
    useScrollReveal: function() { return React.useRef(null) },
  }
})

var React = require('react')
var { render, screen: rtlScreen } = require('@testing-library/react')
var HowItWorks = require('../HowItWorks').default

describe('HowItWorks', function() {
  it('renders the section overline', function() {
    render(React.createElement(HowItWorks))
    expect(rtlScreen.getByText('How It Works')).toBeTruthy()
  })

  it('renders the heading', function() {
    render(React.createElement(HowItWorks))
    expect(rtlScreen.getByText('From Impact to Response in Seconds')).toBeTruthy()
  })

  it('renders all 6 stage titles in mobile view', function() {
    render(React.createElement(HowItWorks))
    expect(rtlScreen.getByText('Crash Detected')).toBeTruthy()
    expect(rtlScreen.getByText('AI Analysis')).toBeTruthy()
    expect(rtlScreen.getByText('Emergency Countdown')).toBeTruthy()
    expect(rtlScreen.getByText('SOS Triggered')).toBeTruthy()
    expect(rtlScreen.getByText('Hospital Routing')).toBeTruthy()
    expect(rtlScreen.getByText('Family Tracking')).toBeTruthy()
  })

  it('renders stage descriptions', function() {
    render(React.createElement(HowItWorks))
    expect(rtlScreen.getByText(/AI-powered accelerometer detects impact/)).toBeTruthy()
    expect(rtlScreen.getByText(/Machine learning classifies severity/)).toBeTruthy()
    expect(rtlScreen.getByText(/Emergency services notified with precise GPS/)).toBeTruthy()
  })

  it('renders stage number indicators', function() {
    render(React.createElement(HowItWorks))
    expect(rtlScreen.getByText('01')).toBeTruthy()
    expect(rtlScreen.getByText('02')).toBeTruthy()
    expect(rtlScreen.getByText('03')).toBeTruthy()
    expect(rtlScreen.getByText('04')).toBeTruthy()
    expect(rtlScreen.getByText('05')).toBeTruthy()
    expect(rtlScreen.getByText('06')).toBeTruthy()
  })
})
