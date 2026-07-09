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
var TechStack = require('../TechStack').default

describe('TechStack', function() {
  it('renders the technology label', function() {
    render(React.createElement(TechStack))
    expect(screen.getByText('TECHNOLOGY')).toBeTruthy()
  })

  it('renders the heading', function() {
    render(React.createElement(TechStack))
    expect(screen.getByText('Built for Scale')).toBeTruthy()
  })

  it('renders inner ring tech names', function() {
    render(React.createElement(TechStack))
    var nextJsNodes = screen.getAllByText('Next.js')
    expect(nextJsNodes.length).toBeGreaterThanOrEqual(1)
    var fastApiNodes = screen.getAllByText('FastAPI')
    expect(fastApiNodes.length).toBeGreaterThanOrEqual(1)
    var supabaseNodes = screen.getAllByText('Supabase')
    expect(supabaseNodes.length).toBeGreaterThanOrEqual(1)
  })

  it('renders middle ring tech names', function() {
    render(React.createElement(TechStack))
    var geminiNodes = screen.getAllByText('Gemini AI')
    expect(geminiNodes.length).toBeGreaterThanOrEqual(1)
    var mapboxNodes = screen.getAllByText('Mapbox')
    expect(mapboxNodes.length).toBeGreaterThanOrEqual(1)
    var threeNodes = screen.getAllByText('Three.js')
    expect(threeNodes.length).toBeGreaterThanOrEqual(1)
  })

  it('renders outer ring tech names', function() {
    render(React.createElement(TechStack))
    var gsapNodes = screen.getAllByText('GSAP')
    expect(gsapNodes.length).toBeGreaterThanOrEqual(1)
    var tfNodes = screen.getAllByText('TensorFlow')
    expect(tfNodes.length).toBeGreaterThanOrEqual(1)
    var dockerNodes = screen.getAllByText('Docker')
    expect(dockerNodes.length).toBeGreaterThanOrEqual(1)
  })

  it('renders the shield SVG logo', function() {
    render(React.createElement(TechStack))
    expect(screen.getByText('SVA')).toBeTruthy()
  })
})
