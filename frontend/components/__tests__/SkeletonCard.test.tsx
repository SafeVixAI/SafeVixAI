// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
import { render } from '@testing-library/react'
import React from 'react'
import SkeletonCard from '../dashboard/SkeletonCard'

describe('SkeletonCard', function () {
  it('renders skeleton structure', function () {
    const container = render(React.createElement(SkeletonCard, null))
    expect(container.container.querySelector('.animate-pulse')).toBeInTheDocument()
  })

  it('applies custom className', function () {
    const container = render(React.createElement(SkeletonCard, { className: 'custom-class' }))
    expect(container.container.querySelector('.custom-class')).toBeInTheDocument()
  })
})
