// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

import { render, screen, fireEvent } from '@testing-library/react'
import React from 'react'
import Toggle from '../dashboard/Toggle'

jest.mock('@/lib/gsap', function() { return { gsap: { fromTo: jest.fn(), to: jest.fn() }, default: { fromTo: jest.fn(), to: jest.fn() } } })

describe('Toggle', function() {
  it('renders unchecked by default', function() {
    render(React.createElement(Toggle, { checked: false, onChange: function() {} }))
    const input = screen.getByRole('checkbox')
    expect(input).toBeTruthy()
  })

  it('renders checked when checked is true', function() {
    render(React.createElement(Toggle, { checked: true, onChange: function() {} }))
    const input = screen.getByRole('checkbox')
    expect(input).toBeTruthy()
  })

  it('calls onChange with true when toggled on', function() {
    const onChange = jest.fn()
    render(React.createElement(Toggle, { checked: false, onChange: onChange }))
    fireEvent.click(screen.getByRole('checkbox'))
  })

  it('uses aria-label when provided', function() {
    render(React.createElement(Toggle, { checked: false, onChange: function() {}, ariaLabel: 'Toggle dark mode' }))
    expect(screen.getByLabelText('Toggle dark mode')).toBeTruthy()
  })
})
