// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
import { render, screen } from '@testing-library/react'
import React from 'react'

jest.mock('next/image', function () { return function MockImg(props: any) { return React.createElement('img', props) } })

describe('HazardViewfinder', function () {
  it('renders default state with detection', async function () {
    const HazardViewfinder = (await import('../report/HazardViewfinder')).default
    render(React.createElement(HazardViewfinder, null))
    expect(screen.getByText('Live hazard viewport')).toBeInTheDocument()
    expect(screen.getByText('Analyzing risk...')).toBeInTheDocument()
  })

  it('renders with image src and not detecting', async function () {
    const HazardViewfinder = (await import('../report/HazardViewfinder')).default
    render(React.createElement(HazardViewfinder, { imageSrc: '/test.jpg', isDetecting: false }))
    expect(screen.getByText('Ready to dispatch')).toBeInTheDocument()
  })

  it('renders custom labels', async function () {
    const HazardViewfinder = (await import('../report/HazardViewfinder')).default
    render(React.createElement(HazardViewfinder, { statusLabel: 'Custom Status', signalLabel: 'Strong', locationLabel: 'Chennai' }))
    expect(screen.getByText('Custom Status')).toBeInTheDocument()
  })

  it('renders with custom confidence value', async function () {
    const HazardViewfinder = (await import('../report/HazardViewfinder')).default
    render(React.createElement(HazardViewfinder, { confidence: 75.5 }))
    expect(screen.getByText(/75\.5/)).toBeInTheDocument()
  })
})
