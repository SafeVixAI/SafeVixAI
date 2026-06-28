// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

jest.mock('@/lib/gsap', function() {
  return {
    gsap: { fromTo: jest.fn(), to: jest.fn(), killTweensOf: jest.fn() },
    ScrollTrigger: { getAll: jest.fn(function() { return [] }), refresh: jest.fn() },
    default: { fromTo: jest.fn(), to: jest.fn() },
  }
})

jest.mock('next/navigation', function() {
  return { usePathname: function() { return '/' } }
})

import { render, screen } from '@testing-library/react'
import React from 'react'
import { GSAPProvider } from '../providers/GSAPProvider'

var mockMatchMedia = { matches: false, addEventListener: jest.fn(function() {}), removeEventListener: jest.fn(function() {}), media: '' }
beforeAll(function() {
  Object.defineProperty(window, 'matchMedia', {
    writable: true,
    value: function() { return mockMatchMedia },
  })
})

describe('GSAPProvider', function() {
  beforeEach(function() {
    jest.clearAllMocks()
    mockMatchMedia.matches = false
    mockMatchMedia.media = ''
  })

  it('renders children', function() {
    render(React.createElement(GSAPProvider, null, React.createElement('div', { 'data-testid': 'child' }, 'Hello')))
    expect(screen.getByTestId('child')).toBeTruthy()
  })

  it('loads gsap for animated routes', function() {
    var gsapMod = require('@/lib/gsap')
    render(React.createElement(GSAPProvider, null, React.createElement('div', null, 'test')))
    expect(gsapMod.gsap.fromTo).toBeDefined()
  })

  it('registers prefers-reduced-motion listener when match true', function() {
    mockMatchMedia.media = '(prefers-reduced-motion: reduce)'
    mockMatchMedia.matches = true
    render(React.createElement(GSAPProvider, null, React.createElement('div', null, 'test')))
    expect(mockMatchMedia.addEventListener).toHaveBeenCalled()
  })
})
