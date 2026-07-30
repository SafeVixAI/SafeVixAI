// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
import { render, screen, fireEvent } from '@testing-library/react'
import React from 'react'
import { EmptyState } from '../ui/EmptyState'

describe('EmptyStateUI', function () {
  it('renders title and description', function () {
    render(React.createElement(EmptyState, { title: 'No Data' }))
    expect(screen.getByText('No Data')).toBeInTheDocument()
  })

  it('renders with description and action', function () {
    const onClick = jest.fn()
    render(React.createElement(EmptyState, { title: 'Empty', description: 'Nothing here', action: { label: 'Retry', onClick: onClick } }))
    expect(screen.getByText('Nothing here')).toBeInTheDocument()
    fireEvent.click(screen.getByText('Retry'))
    expect(onClick).toHaveBeenCalled()
  })

  it('renders with custom className', function () {
    const container = render(React.createElement(EmptyState, { title: 'Test', className: 'custom-class' }))
    expect(container.container.querySelector('.custom-class')).toBeInTheDocument()
  })
})
