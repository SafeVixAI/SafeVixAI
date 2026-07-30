// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

jest.mock('@/lib/client-logger', function() {
  return { logClientError: jest.fn() }
})

import { render, act } from '@testing-library/react'
import React from 'react'
import CameraViewport from '../first-aid/CameraViewport'

describe('CameraViewport', function() {
  beforeEach(function() {
    delete window.MediaStream
    delete window.MediaStreamTrack
  })

  it('renders camera view when media accessible', async function() {
    const mockStream = { getTracks: jest.fn(function() { return [{ stop: jest.fn() }] }) }
    Object.defineProperty(global.navigator, 'mediaDevices', {
      value: {
        getUserMedia: jest.fn(function() { return Promise.resolve(mockStream) }),
      },
      configurable: true,
    })
    const onError = jest.fn()
    await act(async function() {
      render(React.createElement(CameraViewport, { onError: onError }))
    })
    expect(onError).toHaveBeenCalledWith(null)
  })

  it('shows error when camera denied', async function() {
    Object.defineProperty(global.navigator, 'mediaDevices', {
      value: {
        getUserMedia: jest.fn(function() { return Promise.reject(new Error('NotAllowedError')) }),
      },
      configurable: true,
    })
    const onError = jest.fn()
    await act(async function() {
      render(React.createElement(CameraViewport, { onError: onError }))
    })
    expect(onError).toHaveBeenCalledWith('Camera Access Denied')
  })
})
