jest.mock('@/lib/analytics', function() {
  return { track: { pageLoadTiming: jest.fn() } }
}, { virtual: false })

import { render } from '@testing-library/react'
import React from 'react'

var analyticsMod: any

beforeEach(function() {
  jest.clearAllMocks()
  analyticsMod = require('@/lib/analytics')
})

function TestCase() {
  require('../usePageLoadTiming').usePageLoadTiming()
  return React.createElement('div')
}

describe('usePageLoadTiming', function() {
  it('calls pageLoadTiming when document is complete', function() {
    var orig = Object.getOwnPropertyDescriptor(Document.prototype, 'readyState')
    Object.defineProperty(Document.prototype, 'readyState', { value: 'complete', configurable: true })
    render(React.createElement(TestCase))
    expect(analyticsMod.track.pageLoadTiming).toHaveBeenCalledTimes(1)
    if (orig) Object.defineProperty(Document.prototype, 'readyState', orig)
  })

  it('adds load listener when document is not complete', function() {
    var orig = Object.getOwnPropertyDescriptor(Document.prototype, 'readyState')
    Object.defineProperty(Document.prototype, 'readyState', { value: 'loading', configurable: true })
    var addListener = jest.fn()
    window.addEventListener = addListener
    render(React.createElement(TestCase))
    expect(addListener).toHaveBeenCalledWith('load', expect.any(Function), { once: true })
    if (orig) Object.defineProperty(Document.prototype, 'readyState', orig)
  })
})
