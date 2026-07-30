// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
import { render, screen, fireEvent, act } from '@testing-library/react'
import React from 'react'
import ChallanCalculator from '../ChallanCalculator'
const calculateChallan = require('@/lib/api').calculateChallan
const haptics = require('@/lib/haptics').haptics
const track = require('@/lib/analytics').track

// Required mocks for ChallanCalculator dependencies
jest.mock('@/lib/api', function () {
  return { calculateChallan: jest.fn().mockResolvedValue({ section: '185', description: 'Drunk Driving', amount_due: 10000, source: 'online' }) }
})

jest.mock('@/lib/client-logger', function () {
  return { logClientError: jest.fn() }
})

jest.mock('@/lib/analytics', function () {
  return { track: { challanCalculated: jest.fn() } }
})

jest.mock('@/lib/haptics', function () {
  return { haptics: { light: jest.fn() } }
})

jest.mock('@/lib/intl-formatters', function () {
  return { formatCurrency: jest.fn(function (v: number) { return '₹' + v.toLocaleString() }) }
})

jest.mock('@gsap/react', function () {
  return { useGSAP: jest.fn(function (cb: any, _deps: any) { if (typeof cb === 'function') cb() }) }
})

describe('ChallanCalculator', function () {
  beforeEach(function () {
    jest.clearAllMocks()
  })

  it('renders the calculator form', function () {
    const { container } = render(React.createElement(ChallanCalculator))
    expect(container).toBeDefined()
    expect(screen.getByText(/Violation Protocol|01\. Violation/)).toBeDefined()
  })

  it('renders violation selection grid', function () {
    render(React.createElement(ChallanCalculator))
    const buttons = screen.getAllByRole('radio')
    expect(buttons.length).toBeGreaterThan(0)
  })

  it('renders state jurisdiction selector', function () {
    render(React.createElement(ChallanCalculator))
    const selects = screen.getAllByRole('combobox')
    expect(selects.length).toBeGreaterThan(0)
  })

  it('changes violation on button click', function () {
    render(React.createElement(ChallanCalculator))
    const radios = screen.getAllByRole('radio')
    fireEvent.click(radios[2])
    expect(haptics.light).toHaveBeenCalled()
    expect(radios[2].getAttribute('aria-checked')).toBe('true')
  })

  it('changes vehicle class via select', function () {
    render(React.createElement(ChallanCalculator))
    const selects = screen.getAllByRole('combobox')
    fireEvent.change(selects[0], { target: { value: 'LMV' } })
    expect(haptics.light).toHaveBeenCalled()
  })

  it('changes state via select', function () {
    render(React.createElement(ChallanCalculator))
    const selects = screen.getAllByRole('combobox')
    fireEvent.change(selects[1], { target: { value: 'KA' } })
    expect(haptics.light).toHaveBeenCalled()
  })

  it('toggles repeat offender', function () {
    render(React.createElement(ChallanCalculator))
    const repeatBtn = screen.getByText(/Repeat Offender/i).closest('button')!
    fireEvent.click(repeatBtn)
    expect(haptics.light).toHaveBeenCalled()
    expect(repeatBtn.getAttribute('aria-pressed')).toBe('true')
    fireEvent.click(repeatBtn)
    expect(repeatBtn.getAttribute('aria-pressed')).toBe('false')
  })

  it('shows Calculate Penalty button', function () {
    render(React.createElement(ChallanCalculator))
    expect(screen.getByText(/Calculate Penalty/i)).toBeTruthy()
  })

  it('shows result when API succeeds', async function () {
    render(React.createElement(ChallanCalculator))
    const calcBtn = screen.getByText(/Calculate Penalty/i)
    await act(async function () { fireEvent.click(calcBtn) })
    expect(screen.getByText(/Section 185/i)).toBeTruthy()
    const drunkTexts = screen.getAllByText('Drunk Driving')
    expect(drunkTexts.length).toBeGreaterThanOrEqual(1)
    expect(screen.getByText('ONLINE')).toBeTruthy()
  })

  it('shows error when API fails', async function () {
    calculateChallan.mockRejectedValueOnce(new Error('Network error'))
    render(React.createElement(ChallanCalculator))
    const calcBtn = screen.getByText(/Calculate Penalty/i)
    await act(async function () { fireEvent.click(calcBtn) })
    expect(screen.getByText(/Unable to calculate/i)).toBeTruthy()
  })

  it('shows Processing... while loading', async function () {
    const neverResolve = new Promise(function () {}) // never resolves
    calculateChallan.mockReturnValueOnce(neverResolve)
    render(React.createElement(ChallanCalculator))
    const calcBtn = screen.getByText(/Calculate Penalty/i)
    fireEvent.click(calcBtn)
    expect(screen.getByText(/Processing/i)).toBeTruthy()
  })

  it('shows Repeat Offence tag when repeat is enabled', async function () {
    render(React.createElement(ChallanCalculator))
    const repeatBtn = screen.getByText(/Repeat Offender/i).closest('button')!
    fireEvent.click(repeatBtn)
    const calcBtn = screen.getByText(/Calculate Penalty/i)
    await act(async function () { fireEvent.click(calcBtn) })
    expect(screen.getByText(/Repeat Offence/i)).toBeTruthy()
  })

  it('calls analytics on successful calculation', async function () {
    render(React.createElement(ChallanCalculator))
    const calcBtn = screen.getByText(/Calculate Penalty/i)
    await act(async function () { fireEvent.click(calcBtn) })
    expect(track.challanCalculated).toHaveBeenCalledWith('TN', '185', 10000, false)
  })
})
