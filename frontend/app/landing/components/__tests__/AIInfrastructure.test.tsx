jest.mock('@gsap/react', function() { return { useGSAP: jest.fn() } })
jest.mock('@/lib/gsap', function() { return { gsap: { fromTo: jest.fn(), to: jest.fn(), set: jest.fn() } } })
jest.mock('../../hooks/useLandingGSAP', function() {
  const React = require('react')
  return {
    useScrollReveal: function() { return React.useRef(null) },
  }
})

const React = require('react')
const { render, screen: rtlScreen } = require('@testing-library/react')
const AIInfrastructure = require('../AIInfrastructure').default

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
    const ingestionNodes = rtlScreen.getAllByText('Data Ingestion')
    expect(ingestionNodes.length).toBe(2)
    const aiNodes = rtlScreen.getAllByText('AI Processing')
    expect(aiNodes.length).toBe(2)
    const predictionNodes = rtlScreen.getAllByText('Prediction Engine')
    expect(predictionNodes.length).toBe(2)
    const emergencyNodes = rtlScreen.getAllByText('Emergency Response')
    expect(emergencyNodes.length).toBe(2)
    const analyticsNodes = rtlScreen.getAllByText('Analytics')
    expect(analyticsNodes.length).toBe(2)
  })

  it('renders pipeline descriptions', function() {
    render(React.createElement(AIInfrastructure))
    const descriptions = rtlScreen.getAllByText('Multi-source data collection from sensors, reports, and APIs')
    expect(descriptions.length).toBe(2)
    const aiDescs = rtlScreen.getAllByText('Real-time ML inference with Gemini and edge AI models')
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
