import { render, act, screen } from '@testing-library/react'
import React from 'react'

jest.mock('@/lib/gsap', function() {
  return {
    gsap: {
      fromTo: jest.fn(),
    },
  }
})

function TestCase() {
  const ref = require('../usePageEntry').usePageEntry()
  return React.createElement('div', { ref: ref, 'data-testid': 'container' },
    React.createElement('div', { 'data-testid': 'child' }, 'A'),
    React.createElement('div', { 'data-testid': 'child2' }, 'B'),
  )
}

describe('usePageEntry', function() {
  it('sets children visible initially with reduced motion', function() {
    window.matchMedia = jest.fn().mockImplementation(function() {
      return { matches: true, addEventListener: jest.fn(), removeEventListener: jest.fn() }
    })
    render(React.createElement(TestCase))
    const children = document.querySelectorAll('[data-testid^="child"]')
    expect(children.length).toBe(2)
    children.forEach(function(child) {
      expect((child as HTMLElement).style.opacity).toBe('1')
    })
  })

  it('handles null container ref gracefully', function() {
    function NullCase() {
      const ref = require('../usePageEntry').usePageEntry()
      ref.current = null
      return React.createElement('div', { ref: ref })
    }
    expect(function() { render(React.createElement(NullCase)) }).not.toThrow()
  })

  it('returns a ref object', function() {
    const result = render(React.createElement(TestCase))
    expect(result.container.querySelector('[data-testid="container"]')).toBeInTheDocument()
  })

  it('renders children inside container', function() {
    render(React.createElement(TestCase))
    expect(document.querySelectorAll('[data-testid^="child"]').length).toBe(2)
  })

  it('skips animation with prefers-reduced-motion', function() {
    window.matchMedia = jest.fn().mockImplementation(function() {
      return { matches: true, add: jest.fn(), remove: jest.fn() }
    })
    render(React.createElement(TestCase))
    const children = document.querySelectorAll('[data-testid^="child"]')
    children.forEach(function(child) {
      expect((child as HTMLElement).style.opacity).toBe('1')
      expect((child as HTMLElement).style.transform).toBe('translateY(0)')
    })
  })

  it('applies initial invisible styles when motion not reduced', function() {
    jest.useFakeTimers()
    window.matchMedia = jest.fn().mockImplementation(function() {
      return { matches: false, add: jest.fn(), remove: jest.fn() }
    })
    render(React.createElement(TestCase))
    const children = document.querySelectorAll('[data-testid^="child"]')
    children.forEach(function(child) {
      expect((child as HTMLElement).style.opacity).toBe('0')
      expect((child as HTMLElement).style.transform).toBe('translateY(16px)')
    })
  })
})
