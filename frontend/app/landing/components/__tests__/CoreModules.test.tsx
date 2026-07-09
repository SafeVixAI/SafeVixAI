jest.mock('@gsap/react', function() { return { useGSAP: jest.fn() } })
jest.mock('@/lib/gsap', function() { return { gsap: { fromTo: jest.fn(), to: jest.fn(), set: jest.fn() } } })
jest.mock('../../hooks/useLandingGSAP', function() {
  var React = require('react')
  return {
    useScrollReveal: function() { return React.useRef(null) },
  }
})

var React = require('react')
var { render, screen } = require('@testing-library/react')
var CoreModules = require('../CoreModules').default

describe('CoreModules', function() {
  it('renders the section overline', function() {
    render(React.createElement(CoreModules))
    expect(screen.getByText('Core Modules')).toBeTruthy()
  })

  it('renders the heading', function() {
    render(React.createElement(CoreModules))
    expect(screen.getByText('Intelligence Modules')).toBeTruthy()
  })

  it('renders all 3 module names', function() {
    render(React.createElement(CoreModules))
    expect(screen.getByText('RoadSOS')).toBeTruthy()
    expect(screen.getByText('DriveLegal')).toBeTruthy()
    expect(screen.getByText('RoadWatch')).toBeTruthy()
  })

  it('renders module taglines', function() {
    render(React.createElement(CoreModules))
    expect(screen.getByText('AI-Powered Emergency Response')).toBeTruthy()
    expect(screen.getByText('Intelligent Challan Management')).toBeTruthy()
    expect(screen.getByText('Crowd-Powered Hazard Intelligence')).toBeTruthy()
  })

  it('renders RoadSOS features', function() {
    render(React.createElement(CoreModules))
    expect(screen.getByText('AI Crash Detection')).toBeTruthy()
    expect(screen.getByText('SOS Activation')).toBeTruthy()
    expect(screen.getByText('Emergency Routing')).toBeTruthy()
    expect(screen.getByText('Hospital Communication')).toBeTruthy()
    expect(screen.getByText('Family Live Tracking')).toBeTruthy()
  })

  it('renders DriveLegal features', function() {
    render(React.createElement(CoreModules))
    expect(screen.getByText('Challan Intelligence')).toBeTruthy()
    expect(screen.getByText('Fine Analysis')).toBeTruthy()
    expect(screen.getByText('Legal Guidance')).toBeTruthy()
    expect(screen.getByText('Motor Vehicle Act')).toBeTruthy()
    expect(screen.getByText('Penalty Calculator')).toBeTruthy()
  })

  it('renders RoadWatch features', function() {
    render(React.createElement(CoreModules))
    expect(screen.getByText('Hazard Reporting')).toBeTruthy()
    expect(screen.getByText('Crowd Intelligence')).toBeTruthy()
    expect(screen.getByText('Road Condition Monitoring')).toBeTruthy()
    expect(screen.getByText('Infrastructure Awareness')).toBeTruthy()
    expect(screen.getByText('Pothole Detection')).toBeTruthy()
  })

  it('renders Explore buttons for each module', function() {
    render(React.createElement(CoreModules))
    var exploreButtons = screen.getAllByText('Explore')
    expect(exploreButtons.length).toBe(3)
  })

  it('renders the section description', function() {
    render(React.createElement(CoreModules))
    expect(screen.getByText(/Three purpose-built AI modules/)).toBeTruthy()
  })
})
