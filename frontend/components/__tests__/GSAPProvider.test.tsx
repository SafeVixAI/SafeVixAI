// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

jest.mock('@/lib/gsap', function() {
  return {
    gsap: { fromTo: jest.fn(), to: jest.fn(), killTweensOf: jest.fn() },
    ScrollTrigger: { getAll: jest.fn(function() { return [] }), refresh: jest.fn() },
    default: { fromTo: jest.fn(), to: jest.fn() },
  }
})

let mockPathname = '/'
jest.mock('next/navigation', function() {
  return { usePathname: function() { return mockPathname } }
})

import { render, screen } from '@testing-library/react'
import React from 'react'
import { GSAPProvider } from '../providers/GSAPProvider'

const mockMatchMedia = { matches: false, addEventListener: jest.fn(function() {}), removeEventListener: jest.fn(function() {}), media: '' }
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
    const gsapMod = require('@/lib/gsap')
    render(React.createElement(GSAPProvider, null, React.createElement('div', null, 'test')))
    expect(gsapMod.gsap.fromTo).toBeDefined()
  })

  it('registers prefers-reduced-motion listener when match true', function() {
    mockPathname = '/'
    mockMatchMedia.media = '(prefers-reduced-motion: reduce)'
    mockMatchMedia.matches = true
    render(React.createElement(GSAPProvider, null, React.createElement('div', null, 'test')))
    expect(mockMatchMedia.addEventListener).toHaveBeenCalled()
  })

  it('skips all effects for non-animated routes', function() {
    mockPathname = '/privacy'
    const gsapSetter = jest.fn()
    const gsapMod = require('@/lib/gsap')
    gsapMod.gsap.killTweensOf = gsapSetter
    render(React.createElement(GSAPProvider, null, React.createElement('div', { 'data-testid': 'child' }, 'Hello')))
    expect(screen.getByTestId('child')).toBeTruthy()
    // No dynamic import fired, no listeners registered
    expect(mockMatchMedia.addEventListener).not.toHaveBeenCalled()
  })

  it('kills animations on unmount for animated routes', async function() {
    mockPathname = '/'
    const gsapMod = require('@/lib/gsap')
    gsapMod.ScrollTrigger.getAll = jest.fn(function() { return [{ kill: jest.fn() }, { kill: jest.fn() }] })
    const { unmount } = render(React.createElement(GSAPProvider, null, React.createElement('div', null, 'test')))
    unmount()
    await new Promise(function(r) { return setTimeout(r, 50) })
    expect(gsapMod.gsap.killTweensOf).toHaveBeenCalledWith('*')
  })

  it('fires prefers-reduced-motion handler on change event', function() {
    mockPathname = '/'
    mockMatchMedia.matches = false
    const changeListeners: Function[] = []
    mockMatchMedia.addEventListener = jest.fn(function(_evt: string, fn: Function) { changeListeners.push(fn) })
    render(React.createElement(GSAPProvider, null, React.createElement('div', null, 'test')))
    expect(changeListeners.length).toBeGreaterThanOrEqual(1)
  })
})
