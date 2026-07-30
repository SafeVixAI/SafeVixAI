// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

import { render } from '@testing-library/react'
import React from 'react'
import FirstAidCardSkeleton from '../FirstAidCardSkeleton'

describe('FirstAidCardSkeleton', function() {
  it('renders without crashing', function() {
    const el = render(React.createElement(FirstAidCardSkeleton)).container
    expect(el.querySelectorAll('.skeleton').length).toBeGreaterThanOrEqual(4)
  })

  it('renders all skeleton elements', function() {
    const { container } = render(React.createElement(FirstAidCardSkeleton))
    expect(container.querySelectorAll('.skeleton').length).toBe(6)
  })
})
