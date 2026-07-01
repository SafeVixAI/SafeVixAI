// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

jest.mock('@/lib/gsap', function() {
  return { gsap: { fromTo: jest.fn(function() { return {} }), to: jest.fn() }, default: { fromTo: jest.fn(), to: jest.fn() } }
})
jest.mock('@gsap/react', function() {
  return { useGSAP: function(cb) { if (typeof cb === 'function') cb() } }
})

import { render, screen, fireEvent } from '@testing-library/react'
import React from 'react'
import SuggestedInquiries from '../chat/SuggestedInquiries'

describe('SuggestedInquiries', function() {
  it('renders suggestion buttons', function() {
    render(React.createElement(SuggestedInquiries, { onSelect: function() {} }))
    expect(screen.getByText(/\baccident/)).toBeTruthy()
    expect(screen.getByText(/\bambulance/i)).toBeTruthy()
  })

  it('calls onSelect when button clicked', function() {
    var onSelect = jest.fn()
    render(React.createElement(SuggestedInquiries, { onSelect: onSelect }))
    fireEvent.click(screen.getByText(/\baccident/))
    expect(onSelect).toHaveBeenCalled()
  })
})
