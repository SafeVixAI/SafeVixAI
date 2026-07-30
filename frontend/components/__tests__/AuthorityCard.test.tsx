// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

import { render, screen } from '@testing-library/react'
import React from 'react'
import { AuthorityCard } from '../AuthorityCard'

describe('AuthorityCard', function() {
  it('renders authority name', function() {
    render(React.createElement(AuthorityCard))
    expect(screen.getByText('NHAI (Zone 4)')).toBeTruthy()
  })

  it('renders assigned authority label', function() {
    render(React.createElement(AuthorityCard))
    expect(screen.getByText('Assigned Authority')).toBeTruthy()
  })

  it('renders response SLA', function() {
    render(React.createElement(AuthorityCard))
    expect(screen.getByText('Response SLA: 24h')).toBeTruthy()
  })

  it('renders card container', function() {
    const { container } = render(React.createElement(AuthorityCard))
    expect(container.querySelector('.card-glass')).toBeTruthy()
  })
})
