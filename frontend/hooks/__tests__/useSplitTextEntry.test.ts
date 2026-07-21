jest.mock('@gsap/react', function() {
  var React = require('react')
  return {
    useGSAP: function(cb: Function, opts: any) {
      React.useEffect(function() {
        var cleanup = cb()
        return typeof cleanup === 'function' ? cleanup : undefined
      }, [])
    },
  }
})

jest.mock('@/lib/gsap', function() {
  var mockGsap = {
    fromTo: jest.fn().mockReturnValue({ kill: jest.fn() }),
    registerPlugin: jest.fn(),
  }
  return { gsap: mockGsap }
})

import { render } from '@testing-library/react'
import React from 'react'

beforeEach(function() {
  document.body.innerHTML = ''
  window.matchMedia = jest.fn().mockImplementation(function(query: string) {
    return {
      matches: false,
      media: query,
      onchange: null,
      addListener: jest.fn(),
      removeListener: jest.fn(),
      addEventListener: jest.fn(),
      removeEventListener: jest.fn(),
      dispatchEvent: jest.fn(),
    }
  })
})

afterEach(function() {
  jest.restoreAllMocks()
})

function TestCase() {
  var ref = require('../useSplitTextEntry').useSplitTextEntry()
  return React.createElement('h1', { ref, 'data-testid': 'heading' }, 'Hello World')
}

describe('useSplitTextEntry', function() {
  it('returns a heading ref object', function() {
    var result = render(React.createElement(TestCase))
    expect(result.container.querySelector('[data-testid="heading"]')).toBeInTheDocument()
  })

  it('renders heading with text content', function() {
    render(React.createElement(TestCase))
    expect(rtlScreen.getByTestId('heading').textContent).toBe('Hello World')
  })

  it('handles null container ref gracefully', function() {
    function NullCase() {
      var ref = require('../useSplitTextEntry').useSplitTextEntry()
      ref.current = null
      return React.createElement('div', { ref })
    }
    expect(function() { render(React.createElement(NullCase)) }).not.toThrow()
  })

  it('restores original HTML via fallback onComplete callback', function() {
    render(React.createElement(TestCase))
    var gsapMock = require('@/lib/gsap').gsap
    var lastFromTo = gsapMock.fromTo.mock.calls[gsapMock.fromTo.mock.calls.length - 1]
    var config = lastFromTo[2]
    config.onComplete()
    expect(rtlScreen.getByTestId('heading').innerHTML).toBe('Hello World')
  })
})

var { screen: rtlScreen } = require('@testing-library/react')
