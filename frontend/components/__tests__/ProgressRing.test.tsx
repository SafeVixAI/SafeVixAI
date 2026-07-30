jest.mock('@gsap/react', function () { return { useGSAP: jest.fn() } })
jest.mock('@/lib/gsap', function () { return { gsap: { to: jest.fn() } } })

import { render } from '@testing-library/react'
import React from 'react'
import { ProgressRing } from '../crash/ProgressRing'

describe('ProgressRing', function () {
  beforeEach(function () {
    require('@/lib/gsap').gsap.to.mockClear()
  })

  it('renders with default total', function () {
    const container = render(React.createElement(ProgressRing, { seconds: 15 }))
    expect(container.container.querySelector('svg')).toBeInTheDocument()
    expect(container.container.querySelector('[aria-label="15 seconds remaining"]')).toBeInTheDocument()
  })

  it('renders with 5 seconds', function () {
    render(React.createElement(ProgressRing, { seconds: 5 }))
    expect(document.querySelector('svg')).toBeInTheDocument()
  })

  it('does nothing when circleRef is null', function () {
    const useGSAP = require('@gsap/react').useGSAP
    const origImpl = useGSAP.getMockImplementation()
    useGSAP.mockImplementation(function (fn) { fn() })
    const gsapMock = require('@/lib/gsap').gsap
    gsapMock.to.mockClear()
    render(React.createElement(ProgressRing, { seconds: 15 }))
    expect(gsapMock.to).not.toHaveBeenCalled()
    useGSAP.mockImplementation(origImpl)
  })

  it('renders with 1 second', function () {
    render(React.createElement(ProgressRing, { seconds: 1, size: 64 }))
    expect(document.querySelector('svg')).toBeInTheDocument()
  })

  it('invokes useGSAP callback after render', function () {
    const useGSAP = require('@gsap/react').useGSAP
    const capture: Function[] = []
    useGSAP.mockImplementation(function (fn: Function) {
      capture.push(fn)
    })
    render(React.createElement(ProgressRing, { seconds: 5 }))
    expect(capture.length).toBeGreaterThanOrEqual(1)
  })

  it('calls gsap.to when useGSAP callback fires with populated ref', function () {
    const useGSAP = require('@gsap/react').useGSAP
    const capture: Function[] = []
    useGSAP.mockImplementation(function (fn: Function) {
      capture.push(fn)
    })
    render(React.createElement(ProgressRing, { seconds: 3 }))

    const gsapMock = require('@/lib/gsap').gsap
    gsapMock.to.mockClear()

    // After React commits, circleRef.current is populated. Fire the callback.
    const cb = capture[0]
    expect(typeof cb).toBe('function')
    cb()

    expect(gsapMock.to).toHaveBeenCalled()
  })

  it('fires gsap.to with stroke #FF6B6B for seconds=7 (10 < s <= 5)', function () {
    const useGSAP = require('@gsap/react').useGSAP
    const capture: Function[] = []
    useGSAP.mockImplementation(function (fn: Function) { capture.push(fn) })
    render(React.createElement(ProgressRing, { seconds: 7 }))
    const gsapMock = require('@/lib/gsap').gsap
    gsapMock.to.mockClear()
    capture[0]()
    expect(gsapMock.to).toHaveBeenCalledWith(expect.anything(), expect.objectContaining({ stroke: '#FF6B6B' }))
  })

  it('fires gsap.to with stroke #FF0000 for seconds=3', function () {
    const useGSAP = require('@gsap/react').useGSAP
    const capture: Function[] = []
    useGSAP.mockImplementation(function (fn: Function) { capture.push(fn) })
    render(React.createElement(ProgressRing, { seconds: 3 }))
    const gsapMock = require('@/lib/gsap').gsap
    gsapMock.to.mockClear()
    capture[0]()
    expect(gsapMock.to).toHaveBeenCalledWith(expect.anything(), expect.objectContaining({ stroke: '#FF0000' }))
  })

  it('does not change stroke color for seconds > 10', function () {
    const useGSAP = require('@gsap/react').useGSAP
    const capture: Function[] = []
    useGSAP.mockImplementation(function (fn: Function) { capture.push(fn) })
    render(React.createElement(ProgressRing, { seconds: 15 }))
    const gsapMock = require('@/lib/gsap').gsap
    gsapMock.to.mockClear()
    capture[0]()
    const strokeCalls = gsapMock.to.mock.calls.filter(function(c) { return c[1] && c[1].stroke })
    expect(strokeCalls.length).toBe(0)
  })
})
