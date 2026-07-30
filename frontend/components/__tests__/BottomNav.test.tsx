// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
jest.mock('@/lib/gsap', function() {
  return { gsap: { to: jest.fn(), fromTo: jest.fn(function() { return {} }) } }
})

jest.mock('@gsap/react', function() {
  const React2 = require('react');
  return {
    useGSAP: function(cb: any, opts?: any) {
      React2.useEffect(function() {
        if (typeof cb === 'function') cb();
      }, opts?.dependencies || []);
    },
  };
})

import { render, screen, fireEvent } from '@testing-library/react'
import React from 'react'
import BottomNav from '../dashboard/BottomNav'

describe('BottomNav', function () {
  it('renders navigation items', function () {
    render(React.createElement(BottomNav, null))
    expect(screen.getByText('Map')).toBeInTheDocument()
    expect(screen.getByText('AI Chat')).toBeInTheDocument()
    expect(screen.getByText('Locator')).toBeInTheDocument()
  })

  it('renders with aria label', function () {
    render(React.createElement(BottomNav, null))
    expect(screen.getByLabelText('Main navigation')).toBeInTheDocument()
  })

  it('sets aria-current on active link', function () {
    render(React.createElement(BottomNav, null))
    const links = screen.getAllByRole('link')
    const activeLink = links.find(function(l) { return l.getAttribute('aria-current') === 'page' })
    expect(activeLink).toBeDefined()
  })

  it('dispatches vibrate on nav link click', function () {
    const vibrateSpy = jest.fn()
    ;(navigator as any).vibrate = vibrateSpy
    render(React.createElement(BottomNav, null))
    const mapLink = screen.getByText('Map').closest('a')
    fireEvent.click(mapLink!)
    expect(vibrateSpy).toHaveBeenCalledWith(8)
  })

  it('renders Report and First Aid nav items', function () {
    render(React.createElement(BottomNav, null))
    expect(screen.getByText('Report')).toBeInTheDocument()
    expect(screen.getByText('First Aid')).toBeInTheDocument()
  })

  it('renders nav items with correct hrefs', function () {
    render(React.createElement(BottomNav, null))
    const links = screen.getAllByRole('link')
    const locatorLink = links.find(function(l) { return l.getAttribute('href') === '/locator' })
    expect(locatorLink).toBeDefined()
    const chatLink = links.find(function(l) { return l.getAttribute('href') === '/assistant' })
    expect(chatLink).toBeDefined()
  })

  it('uses gsap for indicator animation', function () {
    render(React.createElement(BottomNav, null))
    const gsapMock = require('@/lib/gsap')
    expect(gsapMock.gsap.to).toHaveBeenCalled()
    expect(gsapMock.gsap.fromTo).toHaveBeenCalled()
  })
})
