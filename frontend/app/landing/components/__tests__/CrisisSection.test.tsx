jest.mock('@gsap/react', function() { return { useGSAP: jest.fn() } })
jest.mock('@/lib/gsap', function() { return { gsap: { fromTo: jest.fn(), to: jest.fn(), set: jest.fn() } } })
jest.mock('../../hooks/useLandingGSAP', function() {
  var React = require('react')
  return {
    useScrollReveal: function() { return React.useRef(null) },
    useCountUp: function() { return React.useRef(null) },
  }
})

var React = require('react')
var { render, screen } = require('@testing-library/react')
var CrisisSection = require('../CrisisSection').default

describe('CrisisSection', function() {
  it('renders the crisis overline', function() {
    render(React.createElement(CrisisSection))
    expect(screen.getByText('The Crisis')).toBeTruthy()
  })

  it('renders the subtitle about deadliest roads', function() {
    render(React.createElement(CrisisSection))
    expect(screen.getByText(/deadliest in the world/)).toBeTruthy()
  })

  it('renders all 4 metric cards', function() {
    render(React.createElement(CrisisSection))
    expect(screen.getByText('Road Accidents Annually')).toBeTruthy()
    expect(screen.getByText('Lives Lost Every Year')).toBeTruthy()
    expect(screen.getByText('Die Within First Hour')).toBeTruthy()
    expect(screen.getByText('Hazard Reports Unresolved')).toBeTruthy()
  })

  it('renders the closing statement about 4 minutes', function() {
    render(React.createElement(CrisisSection))
    expect(screen.getByText(/4 minutes/)).toBeTruthy()
  })

  it('renders the metric countdown numbers', function() {
    render(React.createElement(CrisisSection))
    var zeros = screen.getAllByText('0')
    expect(zeros.length).toBeGreaterThanOrEqual(4)
  })
})
