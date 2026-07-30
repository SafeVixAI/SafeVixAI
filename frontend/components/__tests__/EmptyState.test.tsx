// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
import { render, screen } from '@testing-library/react'
import React from 'react'
import EmptyState from '../dashboard/EmptyState'

describe('EmptyState', function () {
  it('renders title and description', function () {
    render(React.createElement(EmptyState, { title: 'No Results', description: 'Nothing to show here' }))
    expect(screen.getByText('No Results')).toBeInTheDocument()
    expect(screen.getByText('Nothing to show here')).toBeInTheDocument()
  })

  it('renders with custom icon', function () {
    const CustomIcon = function () { return React.createElement('svg', { 'data-testid': 'custom-icon' }) }
    render(React.createElement(EmptyState, { title: 'Test', description: 'Desc', icon: CustomIcon as any }))
    expect(screen.getByTestId('custom-icon')).toBeInTheDocument()
  })
})
