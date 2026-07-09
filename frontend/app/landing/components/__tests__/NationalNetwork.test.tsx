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
var NationalNetwork = require('../NationalNetwork').default

describe('NationalNetwork', function() {
  it('renders the section overline', function() {
    render(React.createElement(NationalNetwork))
    expect(screen.getByText('NATIONAL NETWORK')).toBeTruthy()
  })

  it('renders the heading', function() {
    render(React.createElement(NationalNetwork))
    expect(screen.getByText('Connected Intelligence')).toBeTruthy()
  })

  it('renders the section description', function() {
    render(React.createElement(NationalNetwork))
    expect(screen.getByText(/A unified network connecting hospitals/)).toBeTruthy()
  })

  it('renders the India SVG map with aria-label', function() {
    render(React.createElement(NationalNetwork))
    var map = screen.getByRole('img')
    expect(map.getAttribute('aria-label')).toContain('National network map')
  })

  it('renders legend labels', function() {
    render(React.createElement(NationalNetwork))
    expect(screen.getByText('Hospitals')).toBeTruthy()
    expect(screen.getByText('Police')).toBeTruthy()
    expect(screen.getByText('Emergency')).toBeTruthy()
    expect(screen.getByText('Infrastructure')).toBeTruthy()
  })

  it('renders stat counter labels', function() {
    render(React.createElement(NationalNetwork))
    expect(screen.getByText('States Connected')).toBeTruthy()
    expect(screen.getByText('Hospitals Linked')).toBeTruthy()
    expect(screen.getByText('Police Stations')).toBeTruthy()
    expect(screen.getByText('Citizens Protected')).toBeTruthy()
  })

  it('renders descriptive content about end-to-end coverage', function() {
    render(React.createElement(NationalNetwork))
    expect(screen.getByText(/end-to-end coverage/)).toBeTruthy()
  })

  it('renders network status indicator', function() {
    render(React.createElement(NationalNetwork))
    expect(screen.getByText('Network Status: Operational')).toBeTruthy()
  })

  it('renders network status details', function() {
    render(React.createElement(NationalNetwork))
    expect(screen.getByText(/All 28 state nodes online/)).toBeTruthy()
  })
})
