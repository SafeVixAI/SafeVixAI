// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

import { render } from '@testing-library/react'
import React from 'react'
import ServiceCardSkeleton from '../ServiceCardSkeleton'

describe('ServiceCardSkeleton', function() {
  it('renders without crashing', function() {
    const el = render(React.createElement(ServiceCardSkeleton)).container
    expect(el.querySelectorAll('.skeleton').length).toBeGreaterThanOrEqual(5)
  })

  it('renders skeleton elements', function() {
    const { container } = render(React.createElement(ServiceCardSkeleton))
    const skeletons = container.querySelectorAll('.skeleton')
    expect(skeletons.length).toBe(7)
  })
})
