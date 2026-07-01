// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
jest.mock('@gsap/react', function () { return { useGSAP: jest.fn(function(cb) { if (typeof cb === 'function') cb() }) } })

import { render } from '@testing-library/react'
import React from 'react'
import TypingIndicator from '../chat/TypingIndicator'

describe('TypingIndicator', function () {
  it('renders three dots', function () {
    var container = render(React.createElement(TypingIndicator, null))
    var spans = container.container.querySelectorAll('span')
    expect(spans.length).toBe(3)
  })

  it('renders with brand color class', function () {
    var container = render(React.createElement(TypingIndicator, null))
    var spans = container.container.querySelectorAll('span')
    spans.forEach(function (s) { expect(s.className).toContain('bg-brand') })
  })
})
