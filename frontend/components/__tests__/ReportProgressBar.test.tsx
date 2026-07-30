// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
import { render, screen } from '@testing-library/react'
import React from 'react'

describe('ReportProgressBar', function () {
  it('renders all step labels', async function () {
    const _a = await import('../report/ReportProgressBar')
    render(React.createElement(_a.ReportProgressBar, { currentStep: 0 }))
    expect(screen.getByText('Category')).toBeInTheDocument()
    expect(screen.getByText('Location')).toBeInTheDocument()
    expect(screen.getByText('Details')).toBeInTheDocument()
    expect(screen.getByText('Contact')).toBeInTheDocument()
    expect(screen.getByText('Review')).toBeInTheDocument()
  })

  it('shows check marks for completed steps', async function () {
    const _a = await import('../report/ReportProgressBar')
    const container = render(React.createElement(_a.ReportProgressBar, { currentStep: 3 }))
    const checkIcons = container.container.querySelectorAll('svg')
    expect(checkIcons.length).toBeGreaterThan(0)
  })

  it('highlights current step', async function () {
    const _a = await import('../report/ReportProgressBar')
    render(React.createElement(_a.ReportProgressBar, { currentStep: 2 }))
    expect(screen.getByText('Details')).toBeInTheDocument()
  })
})
