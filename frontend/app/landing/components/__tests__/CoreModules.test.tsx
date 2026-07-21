jest.mock('@gsap/react', function() { return { useGSAP: jest.fn() } })
jest.mock('@/lib/gsap', function() { return { gsap: { fromTo: jest.fn(), to: jest.fn(), set: jest.fn() } } })
jest.mock('../../hooks/useLandingGSAP', function() {
  var React = require('react')
  return {
    useScrollReveal: function() { return React.useRef(null) },
  }
})

var React = require('react')
var { render, screen: rtlScreen } = require('@testing-library/react')
var CoreModules = require('../CoreModules').default

describe('CoreModules', function() {
  it('renders the section overline', function() {
    render(React.createElement(CoreModules))
    expect(rtlScreen.getByText('Core Modules')).toBeTruthy()
  })

  it('renders the heading', function() {
    render(React.createElement(CoreModules))
    expect(rtlScreen.getByText('Intelligence Modules')).toBeTruthy()
  })

  it('renders all 3 module names', function() {
    render(React.createElement(CoreModules))
    expect(rtlScreen.getByText('RoadSOS')).toBeTruthy()
    expect(rtlScreen.getByText('DriveLegal')).toBeTruthy()
    expect(rtlScreen.getByText('RoadWatch')).toBeTruthy()
  })

  it('renders module taglines', function() {
    render(React.createElement(CoreModules))
    expect(rtlScreen.getByText('AI-Powered Emergency Response')).toBeTruthy()
    expect(rtlScreen.getByText('Intelligent Challan Management')).toBeTruthy()
    expect(rtlScreen.getByText('Crowd-Powered Hazard Intelligence')).toBeTruthy()
  })

  it('renders RoadSOS features', function() {
    render(React.createElement(CoreModules))
    expect(rtlScreen.getByText('AI Crash Detection')).toBeTruthy()
    expect(rtlScreen.getByText('SOS Activation')).toBeTruthy()
    expect(rtlScreen.getByText('Emergency Routing')).toBeTruthy()
    expect(rtlScreen.getByText('Hospital Communication')).toBeTruthy()
    expect(rtlScreen.getByText('Family Live Tracking')).toBeTruthy()
  })

  it('renders DriveLegal features', function() {
    render(React.createElement(CoreModules))
    expect(rtlScreen.getByText('Challan Intelligence')).toBeTruthy()
    expect(rtlScreen.getByText('Fine Analysis')).toBeTruthy()
    expect(rtlScreen.getByText('Legal Guidance')).toBeTruthy()
    expect(rtlScreen.getByText('Motor Vehicle Act')).toBeTruthy()
    expect(rtlScreen.getByText('Penalty Calculator')).toBeTruthy()
  })

  it('renders RoadWatch features', function() {
    render(React.createElement(CoreModules))
    expect(rtlScreen.getByText('Hazard Reporting')).toBeTruthy()
    expect(rtlScreen.getByText('Crowd Intelligence')).toBeTruthy()
    expect(rtlScreen.getByText('Road Condition Monitoring')).toBeTruthy()
    expect(rtlScreen.getByText('Infrastructure Awareness')).toBeTruthy()
    expect(rtlScreen.getByText('Pothole Detection')).toBeTruthy()
  })

  it('renders Explore buttons for each module', function() {
    render(React.createElement(CoreModules))
    var exploreButtons = rtlScreen.getAllByText('Explore')
    expect(exploreButtons.length).toBe(3)
  })

  it('renders the section description', function() {
    render(React.createElement(CoreModules))
    expect(rtlScreen.getByText(/Three purpose-built AI modules/)).toBeTruthy()
  })
})
