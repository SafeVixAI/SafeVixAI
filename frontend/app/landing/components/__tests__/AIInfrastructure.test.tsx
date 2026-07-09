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
var AIInfrastructure = require('../AIInfrastructure').default

describe('AIInfrastructure', function() {
  it('renders the section overline', function() {
    render(React.createElement(AIInfrastructure))
    expect(screen.getByText('AI INFRASTRUCTURE')).toBeTruthy()
  })

  it('renders the heading', function() {
    render(React.createElement(AIInfrastructure))
    expect(screen.getByText('Intelligence Pipeline')).toBeTruthy()
  })

  it('renders all 5 pipeline node titles', function() {
    render(React.createElement(AIInfrastructure))
    var ingestionNodes = screen.getAllByText('Data Ingestion')
    expect(ingestionNodes.length).toBe(2)
    var aiNodes = screen.getAllByText('AI Processing')
    expect(aiNodes.length).toBe(2)
    var predictionNodes = screen.getAllByText('Prediction Engine')
    expect(predictionNodes.length).toBe(2)
    var emergencyNodes = screen.getAllByText('Emergency Response')
    expect(emergencyNodes.length).toBe(2)
    var analyticsNodes = screen.getAllByText('Analytics')
    expect(analyticsNodes.length).toBe(2)
  })

  it('renders pipeline descriptions', function() {
    render(React.createElement(AIInfrastructure))
    var descriptions = screen.getAllByText('Multi-source data collection from sensors, reports, and APIs')
    expect(descriptions.length).toBe(2)
    var aiDescs = screen.getAllByText('Real-time ML inference with Gemini and edge AI models')
    expect(aiDescs.length).toBe(2)
  })

  it('renders throughput stats', function() {
    render(React.createElement(AIInfrastructure))
    expect(screen.getByText('<4s')).toBeTruthy()
    expect(screen.getByText('10M+')).toBeTruthy()
    expect(screen.getByText('99.97%')).toBeTruthy()
    expect(screen.getByText('28')).toBeTruthy()
  })

  it('renders stat labels', function() {
    render(React.createElement(AIInfrastructure))
    expect(screen.getByText('Response Time')).toBeTruthy()
    expect(screen.getByText('Daily Events')).toBeTruthy()
    expect(screen.getByText('Uptime SLA')).toBeTruthy()
    expect(screen.getByText('State Coverage')).toBeTruthy()
  })
})
