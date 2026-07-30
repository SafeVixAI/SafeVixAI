// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
import { render } from '@testing-library/react'
import React from 'react'
import { SkeletonCard } from '../ui/SkeletonCard'

describe('SkeletonCardUI', function () {
  it('renders with default props', function () {
    const container = render(React.createElement(SkeletonCard, null))
    expect(container.container.querySelector('.sv-skeleton')).toBeInTheDocument()
  })

  it('renders without icon', function () {
    const container = render(React.createElement(SkeletonCard, { hasIcon: false }))
    expect(container.container.querySelector('.sv-skeleton')).toBeInTheDocument()
  })

  it('renders with custom line count and button', function () {
    const container = render(React.createElement(SkeletonCard, { lines: 5, hasButton: true }))
    expect(container.container.querySelector('.sv-skeleton')).toBeInTheDocument()
  })
})
