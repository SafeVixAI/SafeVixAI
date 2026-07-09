jest.mock('@gsap/react', function() { return { useGSAP: jest.fn() } })
jest.mock('@/lib/gsap', function() { return { gsap: { fromTo: jest.fn(), to: jest.fn(), set: jest.fn(), timeline: function() { return { fromTo: jest.fn(), to: jest.fn(), kill: jest.fn() } } } } })
jest.mock('../../hooks/useLandingGSAP', function() {
  var React = require('react')
  return {
    useScrollReveal: function() { return React.useRef(null) },
  }
})

var React = require('react')
var { render, screen } = require('@testing-library/react')
var HowItWorks = require('../HowItWorks').default

describe('HowItWorks', function() {
  it('renders the section overline', function() {
    render(React.createElement(HowItWorks))
    expect(screen.getByText('How It Works')).toBeTruthy()
  })

  it('renders the heading', function() {
    render(React.createElement(HowItWorks))
    expect(screen.getByText('From Impact to Response in Seconds')).toBeTruthy()
  })

  it('renders all 6 stage titles in mobile view', function() {
    render(React.createElement(HowItWorks))
    expect(screen.getByText('Crash Detected')).toBeTruthy()
    expect(screen.getByText('AI Analysis')).toBeTruthy()
    expect(screen.getByText('Emergency Countdown')).toBeTruthy()
    expect(screen.getByText('SOS Triggered')).toBeTruthy()
    expect(screen.getByText('Hospital Routing')).toBeTruthy()
    expect(screen.getByText('Family Tracking')).toBeTruthy()
  })

  it('renders stage descriptions', function() {
    render(React.createElement(HowItWorks))
    expect(screen.getByText(/AI-powered accelerometer detects impact/)).toBeTruthy()
    expect(screen.getByText(/Machine learning classifies severity/)).toBeTruthy()
    expect(screen.getByText(/Emergency services notified with precise GPS/)).toBeTruthy()
  })

  it('renders stage number indicators', function() {
    render(React.createElement(HowItWorks))
    expect(screen.getByText('01')).toBeTruthy()
    expect(screen.getByText('02')).toBeTruthy()
    expect(screen.getByText('03')).toBeTruthy()
    expect(screen.getByText('04')).toBeTruthy()
    expect(screen.getByText('05')).toBeTruthy()
    expect(screen.getByText('06')).toBeTruthy()
  })
})
