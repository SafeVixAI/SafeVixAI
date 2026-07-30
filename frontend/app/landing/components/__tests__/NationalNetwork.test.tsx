jest.mock('@gsap/react', function() { return { useGSAP: jest.fn() } })
jest.mock('@/lib/gsap', function() { return { gsap: { fromTo: jest.fn(), to: jest.fn(), set: jest.fn() } } })
jest.mock('../../hooks/useLandingGSAP', function() {
  const React = require('react')
  return {
    useScrollReveal: function() { return React.useRef(null) },
    useCountUp: function() { return React.useRef(null) },
  }
})

const React = require('react')
const { render, screen: rtlScreen } = require('@testing-library/react')
const NationalNetwork = require('../NationalNetwork').default

describe('NationalNetwork', function() {
  it('renders the section overline', function() {
    render(React.createElement(NationalNetwork))
    expect(rtlScreen.getByText('NATIONAL NETWORK')).toBeTruthy()
  })

  it('renders the heading', function() {
    render(React.createElement(NationalNetwork))
    expect(rtlScreen.getByText('Connected Intelligence')).toBeTruthy()
  })

  it('renders the section description', function() {
    render(React.createElement(NationalNetwork))
    expect(rtlScreen.getByText(/A unified network connecting hospitals/)).toBeTruthy()
  })

  it('renders the India SVG map with aria-label', function() {
    render(React.createElement(NationalNetwork))
    const map = rtlScreen.getByRole('img')
    expect(map.getAttribute('aria-label')).toContain('National network map')
  })

  it('renders legend labels', function() {
    render(React.createElement(NationalNetwork))
    expect(rtlScreen.getByText('Hospitals')).toBeTruthy()
    expect(rtlScreen.getByText('Police')).toBeTruthy()
    expect(rtlScreen.getByText('Emergency')).toBeTruthy()
    expect(rtlScreen.getByText('Infrastructure')).toBeTruthy()
  })

  it('renders stat counter labels', function() {
    render(React.createElement(NationalNetwork))
    expect(rtlScreen.getByText('States Connected')).toBeTruthy()
    expect(rtlScreen.getByText('Hospitals Linked')).toBeTruthy()
    expect(rtlScreen.getByText('Police Stations')).toBeTruthy()
    expect(rtlScreen.getByText('Citizens Protected')).toBeTruthy()
  })

  it('renders descriptive content about end-to-end coverage', function() {
    render(React.createElement(NationalNetwork))
    expect(rtlScreen.getByText(/end-to-end coverage/)).toBeTruthy()
  })

  it('renders network status indicator', function() {
    render(React.createElement(NationalNetwork))
    expect(rtlScreen.getByText('Network Status: Operational')).toBeTruthy()
  })

  it('renders network status details', function() {
    render(React.createElement(NationalNetwork))
    expect(rtlScreen.getByText(/All 28 state nodes online/)).toBeTruthy()
  })
})
