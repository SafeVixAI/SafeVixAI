jest.mock('@gsap/react', function() { return { useGSAP: jest.fn() } })
jest.mock('@/lib/gsap', function() { return { gsap: { fromTo: jest.fn(), to: jest.fn(), set: jest.fn(), timeline: function() { return { fromTo: jest.fn(), to: jest.fn() } } } } })
jest.mock('next/dynamic', function() { return function() { return function() { return React.createElement('div', null, 'Globe Fallback') } } })
jest.mock('next/link', function() { return function({ children, href }) { return React.createElement('a', { href: href }, children) } })

var React = require('react')
const { render, screen: rtlScreen } = require('@testing-library/react')
const HeroSection = require('../HeroSection').default

describe('HeroSection', function() {
  it('renders overline text', function() {
    render(React.createElement(HeroSection))
    expect(rtlScreen.getByText('National Road Safety Intelligence')).toBeTruthy()
  })

  it('renders headline about AI-powered road safety', function() {
    render(React.createElement(HeroSection))
    expect(rtlScreen.getByText(/AI-Powered/)).toBeTruthy()
  })

  it('renders Launch Platform link', function() {
    render(React.createElement(HeroSection))
    expect(rtlScreen.getByText('Launch Platform')).toBeTruthy()
  })

  it('renders Create Account link', function() {
    render(React.createElement(HeroSection))
    expect(rtlScreen.getByText('Create Account')).toBeTruthy()
  })

  it('renders Explore Intelligence link', function() {
    render(React.createElement(HeroSection))
    expect(rtlScreen.getByText('Explore Intelligence')).toBeTruthy()
  })

  it('renders system status indicator', function() {
    render(React.createElement(HeroSection))
    expect(rtlScreen.getByText('System Online — Monitoring Active')).toBeTruthy()
  })
})
