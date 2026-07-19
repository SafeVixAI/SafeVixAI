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
var AIInfrastructure = require('../AIInfrastructure').default

describe('AIInfrastructure', function() {
  it('renders the section overline', function() {
    render(React.createElement(AIInfrastructure))
    expect(rtlScreen.getByText('AI INFRASTRUCTURE')).toBeTruthy()
  })

  it('renders the heading', function() {
    render(React.createElement(AIInfrastructure))
    expect(rtlScreen.getByText('Intelligence Pipeline')).toBeTruthy()
  })

  it('renders all 5 pipeline node titles', function() {
    render(React.createElement(AIInfrastructure))
    var ingestionNodes = rtlScreen.getAllByText('Data Ingestion')
    expect(ingestionNodes.length).toBe(2)
    var aiNodes = rtlScreen.getAllByText('AI Processing')
    expect(aiNodes.length).toBe(2)
    var predictionNodes = rtlScreen.getAllByText('Prediction Engine')
    expect(predictionNodes.length).toBe(2)
    var emergencyNodes = rtlScreen.getAllByText('Emergency Response')
    expect(emergencyNodes.length).toBe(2)
    var analyticsNodes = rtlScreen.getAllByText('Analytics')
    expect(analyticsNodes.length).toBe(2)
  })

  it('renders pipeline descriptions', function() {
    render(React.createElement(AIInfrastructure))
    var descriptions = rtlScreen.getAllByText('Multi-source data collection from sensors, reports, and APIs')
    expect(descriptions.length).toBe(2)
    var aiDescs = rtlScreen.getAllByText('Real-time ML inference with Gemini and edge AI models')
    expect(aiDescs.length).toBe(2)
  })

  it('renders throughput stats', function() {
    render(React.createElement(AIInfrastructure))
    expect(rtlScreen.getByText('<4s')).toBeTruthy()
    expect(rtlScreen.getByText('10M+')).toBeTruthy()
    expect(rtlScreen.getByText('99.97%')).toBeTruthy()
    expect(rtlScreen.getByText('28')).toBeTruthy()
  })

  it('renders stat labels', function() {
    render(React.createElement(AIInfrastructure))
    expect(rtlScreen.getByText('Response Time')).toBeTruthy()
    expect(rtlScreen.getByText('Daily Events')).toBeTruthy()
    expect(rtlScreen.getByText('Uptime SLA')).toBeTruthy()
    expect(rtlScreen.getByText('State Coverage')).toBeTruthy()
  })
})
