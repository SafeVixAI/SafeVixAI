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
var TechStack = require('../TechStack').default

describe('TechStack', function() {
  it('renders the technology label', function() {
    render(React.createElement(TechStack))
    expect(rtlScreen.getByText('TECHNOLOGY')).toBeTruthy()
  })

  it('renders the heading', function() {
    render(React.createElement(TechStack))
    expect(rtlScreen.getByText('Built for Scale')).toBeTruthy()
  })

  it('renders inner ring tech names', function() {
    render(React.createElement(TechStack))
    var nextJsNodes = rtlScreen.getAllByText('Next.js')
    expect(nextJsNodes.length).toBeGreaterThanOrEqual(1)
    var fastApiNodes = rtlScreen.getAllByText('FastAPI')
    expect(fastApiNodes.length).toBeGreaterThanOrEqual(1)
    var supabaseNodes = rtlScreen.getAllByText('Supabase')
    expect(supabaseNodes.length).toBeGreaterThanOrEqual(1)
  })

  it('renders middle ring tech names', function() {
    render(React.createElement(TechStack))
    var geminiNodes = rtlScreen.getAllByText('Gemini AI')
    expect(geminiNodes.length).toBeGreaterThanOrEqual(1)
    var mapboxNodes = rtlScreen.getAllByText('Mapbox')
    expect(mapboxNodes.length).toBeGreaterThanOrEqual(1)
    var threeNodes = rtlScreen.getAllByText('Three.js')
    expect(threeNodes.length).toBeGreaterThanOrEqual(1)
  })

  it('renders outer ring tech names', function() {
    render(React.createElement(TechStack))
    var gsapNodes = rtlScreen.getAllByText('GSAP')
    expect(gsapNodes.length).toBeGreaterThanOrEqual(1)
    var tfNodes = rtlScreen.getAllByText('TensorFlow')
    expect(tfNodes.length).toBeGreaterThanOrEqual(1)
    var dockerNodes = rtlScreen.getAllByText('Docker')
    expect(dockerNodes.length).toBeGreaterThanOrEqual(1)
  })

  it('renders the shield SVG logo', function() {
    render(React.createElement(TechStack))
    expect(rtlScreen.getByText('SVA')).toBeTruthy()
  })
})
