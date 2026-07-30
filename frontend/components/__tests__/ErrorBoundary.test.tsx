// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

import { render, screen, fireEvent } from '@testing-library/react'
import React from 'react'
import ErrorBoundary from '../ui/ErrorBoundary'

const ErrorThrower = function() {
  throw new Error('Test error')
}

const SafeComponent = function() {
  return React.createElement('div', { 'data-testid': 'safe-child' }, 'All good')
}

describe('ErrorBoundary', function() {
  beforeEach(function() {
    jest.spyOn(console, 'error').mockImplementation(function() {})
  })

  afterEach(function() {
    jest.restoreAllMocks()
  })

  it('renders children when no error', function() {
    render(React.createElement(ErrorBoundary, null, React.createElement(SafeComponent)))
    expect(screen.getByTestId('safe-child')).toBeTruthy()
  })

  it('renders default error UI when child throws', function() {
    render(React.createElement(ErrorBoundary, null, React.createElement(ErrorThrower)))
    expect(screen.getByText('Something went wrong')).toBeTruthy()
    expect(screen.getByText('Retry')).toBeTruthy()
    expect(screen.getByRole('alert')).toBeTruthy()
  })

  it('renders custom fallback instead of default', function() {
    const CustomFallback = function() {
      return React.createElement('div', { 'data-testid': 'custom-fallback' }, 'Custom error')
    }
    render(React.createElement(ErrorBoundary, { fallback: React.createElement(CustomFallback) }, React.createElement(ErrorThrower)))
    expect(screen.getByTestId('custom-fallback')).toBeTruthy()
  })

  it('includes name in error message when provided', function() {
    render(React.createElement(ErrorBoundary, { name: 'TestWidget' }, React.createElement(ErrorThrower)))
    expect(screen.getByText(/TestWidget/)).toBeTruthy()
  })

  it('Retry button does not throw', function() {
    render(React.createElement(ErrorBoundary, null, React.createElement(ErrorThrower)))
    expect(function() { fireEvent.click(screen.getByText('Retry')) }).not.toThrow()
  })

  it('calls onError callback when error occurs', function() {
    const onError = jest.fn()
    render(React.createElement(ErrorBoundary, { onError: onError }, React.createElement(ErrorThrower)))
    expect(onError).toHaveBeenCalledTimes(1)
    expect(onError.mock.calls[0][0]).toBeInstanceOf(Error)
    expect(onError.mock.calls[0][0].message).toBe('Test error')
  })
})
