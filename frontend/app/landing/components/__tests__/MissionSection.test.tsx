jest.mock('@/app/landing/hooks/useLandingGSAP', function() { return { useTextReveal: function() { return { current: null } }, useScrollReveal: function() { return function() { return { current: null } } } } })

const React = require('react')
const { render, screen: rtlScreen } = require('@testing-library/react')
const MissionSection = require('../MissionSection').default

describe('MissionSection', function() {
  it('renders section with id mission', function() {
    const { container } = render(React.createElement(MissionSection))
    const section = container.querySelector('#mission')
    expect(section).toBeTruthy()
  })

  it('renders heading about road safety intelligence', function() {
    render(React.createElement(MissionSection))
    expect(rtlScreen.getByText(/Building India.*Next Generation.*Road Safety/)).toBeTruthy()
  })

  it('renders sub text about seconds and lives', function() {
    render(React.createElement(MissionSection))
    expect(rtlScreen.getByText(/Every second counts/)).toBeTruthy()
  })

  it('renders shield SVG', function() {
    const { container } = render(React.createElement(MissionSection))
    const svg = container.querySelector('svg')
    expect(svg).toBeTruthy()
    expect(svg.getAttribute('aria-hidden')).toBe('true')
  })

  it('renders with landing-section class', function() {
    const { container } = render(React.createElement(MissionSection))
    expect(container.querySelector('.landing-section')).toBeTruthy()
  })

  it('renders ambient light gradients', function() {
    const { container } = render(React.createElement(MissionSection))
    const divs = container.querySelectorAll('[class*="pointer-events-none"]')
    expect(divs.length).toBeGreaterThanOrEqual(2)
  })

  it('renders heading with font-space class', function() {
    const { container } = render(React.createElement(MissionSection))
    const heading = container.querySelector('.font-space')
    expect(heading).toBeTruthy()
  })

  it('renders description paragraph with reveal-item', function() {
    const { container } = render(React.createElement(MissionSection))
    const paragraphs = container.querySelectorAll('.reveal-item')
    expect(paragraphs.length).toBeGreaterThan(0)
  })

  it('renders SVA text in shield', function() {
    render(React.createElement(MissionSection))
    expect(rtlScreen.getByText('SVA')).toBeTruthy()
  })
})
