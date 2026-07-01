// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

import { render, screen } from '@testing-library/react'
import React from 'react'
import { LeadershipCard } from '../guide/LeadershipCard'

var mockMunicipality = {
  mayorName: 'John Doe',
  commissionerName: 'Jane Smith',
  commissionerPhone: '1234567890',
}

jest.mock('@/lib/api', function() { return { MunicipalityDetail: {} } })

describe('LeadershipCard', function() {
  it('renders mayor name', function() {
    render(React.createElement(LeadershipCard, { municipality: mockMunicipality as any }))
    expect(screen.getByText('Mayor')).toBeTruthy()
    expect(screen.getByText('John Doe')).toBeTruthy()
  })

  it('renders commissioner name', function() {
    render(React.createElement(LeadershipCard, { municipality: mockMunicipality as any }))
    expect(screen.getByText('Commissioner')).toBeTruthy()
    expect(screen.getByText('Jane Smith')).toBeTruthy()
  })

  it('renders phone link when available', function() {
    render(React.createElement(LeadershipCard, { municipality: mockMunicipality as any }))
    var phoneLink = screen.getByText('1234567890').closest('a')
    expect(phoneLink?.getAttribute('href')).toBe('tel:1234567890')
  })

  it('shows initials in avatar', function() {
    render(React.createElement(LeadershipCard, { municipality: mockMunicipality as any }))
    expect(screen.getByText('JD')).toBeTruthy()
    expect(screen.getByText('JS')).toBeTruthy()
  })

  it('shows "Information not available" when name is null', function() {
    render(React.createElement(LeadershipCard, { municipality: { mayorName: null, commissionerName: null } as any }))
    expect(screen.getAllByText('Information not available')).toHaveLength(2)
  })

  it('does not render phone link when phone is null', function() {
    render(React.createElement(LeadershipCard, { municipality: { mayorName: 'John', commissionerName: 'Jane', commissionerPhone: null } as any }))
    expect(screen.queryByText('1234567890')).toBeNull()
  })

  it('computes initials from single word name', function() {
    render(React.createElement(LeadershipCard, { municipality: { mayorName: 'John', commissionerName: 'Doe', commissionerPhone: '999' } as any }))
    expect(screen.getByText('J')).toBeTruthy()
  })

  it('renders User icon when name is null', function() {
    var { container } = render(React.createElement(LeadershipCard, { municipality: { mayorName: null, commissionerName: null } as any }))
    // Should render lucide User icon (SVG) instead of initials text
    expect(container.querySelector('svg')).toBeTruthy()
  })
})
