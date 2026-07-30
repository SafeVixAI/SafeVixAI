// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

import { render } from '@testing-library/react'
import React from 'react'
import MessageBubbleSkeleton, { ChatSkeleton } from '../chat/MessageBubbleSkeleton'

describe('MessageBubbleSkeleton', function() {
  it('renders user bubble', function() {
    const { container } = render(React.createElement(MessageBubbleSkeleton, { isUser: true }))
    expect(container.querySelector('.justify-end')).toBeTruthy()
  })

  it('renders bot bubble', function() {
    const { container } = render(React.createElement(MessageBubbleSkeleton, { isUser: false }))
    expect(container.querySelector('.justify-start')).toBeTruthy()
  })

  it('renders default (bot) when no isUser prop', function() {
    const { container } = render(React.createElement(MessageBubbleSkeleton))
    expect(container.querySelector('.justify-start')).toBeTruthy()
  })
})

describe('ChatSkeleton', function() {
  it('renders 3 bubbles', function() {
    const { container } = render(React.createElement(ChatSkeleton))
    expect(container.querySelectorAll('.skeleton').length).toBeGreaterThanOrEqual(3)
  })
})
