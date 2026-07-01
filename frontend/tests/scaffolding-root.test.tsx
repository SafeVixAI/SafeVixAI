jest.mock('next/image', function() { return function(props) { return React.createElement('img', props) } })
jest.mock('lucide-react', function() { return new Proxy({}, { get: function() { return function() { return null } } }) })
jest.mock('@/lib/client-logger', function() { return { logClientError: jest.fn() } })

import { render, screen, fireEvent } from '@testing-library/react'
import React from 'react'
import { logClientError } from '@/lib/client-logger'

import NotFound from '@/app/not-found'
import { PrintButton } from '@/app/emergency-card/[userId]/PrintButton'
import GlobalError from '@/app/error'

describe('Root app components', function() {
  beforeEach(function() { jest.clearAllMocks() })

  it('renders not-found page with links', function() {
    render(React.createElement(NotFound))
    expect(screen.getByText('This page does not exist')).toBeTruthy()
    expect(screen.getByText('Go Home')).toBeTruthy()
  })

  it('renders PrintButton and calls window.print on click', function() {
    var printSpy = jest.spyOn(window, 'print').mockImplementation(function() {})
    render(React.createElement(PrintButton))
    expect(screen.getByText('Print / Save')).toBeTruthy()
    fireEvent.click(screen.getByText('Print / Save'))
    expect(printSpy).toHaveBeenCalled()
    printSpy.mockRestore()
  })

  it('renders root error boundary with error details', function() {
    var testError = new Error('Root crash')
    ;(testError as any).digest = 'abc123'
    render(React.createElement(GlobalError, { error: testError, reset: jest.fn() }))
    expect(logClientError).toHaveBeenCalled()
    expect(screen.getByText('Digest: abc123')).toBeTruthy()
  })

  it('root error renders without digest when digest missing', function() {
    var testError = new Error('No digest')
    render(React.createElement(GlobalError, { error: testError, reset: jest.fn() }))
    expect(screen.queryByText(/Digest:/)).toBeNull()
  })
})
