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
var { render, screen: rtlScreen } = require('@testing-library/react')
var CrisisSection = require('../CrisisSection').default

describe('CrisisSection', function() {
  it('renders the crisis overline', function() {
    render(React.createElement(CrisisSection))
    expect(rtlScreen.getByText('The Crisis')).toBeTruthy()
  })

  it('renders the subtitle about deadliest roads', function() {
    render(React.createElement(CrisisSection))
    expect(rtlScreen.getByText(/deadliest in the world/)).toBeTruthy()
  })

  it('renders all 4 metric cards', function() {
    render(React.createElement(CrisisSection))
    expect(rtlScreen.getByText('Road Accidents Annually')).toBeTruthy()
    expect(rtlScreen.getByText('Lives Lost Every Year')).toBeTruthy()
    expect(rtlScreen.getByText('Die Within First Hour')).toBeTruthy()
    expect(rtlScreen.getByText('Hazard Reports Unresolved')).toBeTruthy()
  })

  it('renders the closing statement about 4 minutes', function() {
    render(React.createElement(CrisisSection))
    expect(rtlScreen.getByText(/4 minutes/)).toBeTruthy()
  })

  it('renders the metric countdown numbers', function() {
    render(React.createElement(CrisisSection))
    var zeros = rtlScreen.getAllByText('0')
    expect(zeros.length).toBeGreaterThanOrEqual(4)
  })
})
