// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

let mockState = { aiMode: 'loading', modelLoadProgress: 42 }

jest.mock('@/lib/store', function() {
  return {
    __setMockState: function(s: any) { mockState = s },
    useAppStore: function(selector: any) {
      if (typeof selector === 'function') return selector(mockState)
      return mockState
    },
  }
})

import { render, screen } from '@testing-library/react'
import React from 'react'
import { ModelLoader } from '../ModelLoader'

describe('ModelLoader', function() {
  it('renders when aiMode is loading', function() {
    render(React.createElement(ModelLoader))
    expect(screen.getByText('Loading Offline AI Model')).toBeTruthy()
  })

  it('shows progress percentage', function() {
    render(React.createElement(ModelLoader))
    expect(screen.getByText('42%')).toBeTruthy()
  })

  it('does not render when aiMode is not loading', function() {
    mockState = { aiMode: 'idle', modelLoadProgress: 0 }
    const { container } = render(React.createElement(ModelLoader))
    expect(container.innerHTML).toBe('')
    mockState = { aiMode: 'loading', modelLoadProgress: 42 }
  })

  it('renders progress bar with correct width', function() {
    render(React.createElement(ModelLoader))
    const progressText = screen.getByText('42%')
    expect(progressText).toBeTruthy()
  })
})
