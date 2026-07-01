// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

import { render, screen } from '@testing-library/react'
import React from 'react'
import { ContactChannels } from '../guide/ContactChannels'

var mockMunicipality = {
  headquartersAddress: '123 Main St, Chennai',
  helplinePhone: '1800-123-4567',
  email: 'help@municipality.gov.in',
  websiteUrl: 'https://municipality.gov.in',
  whatsappNumber: '919876543210',
  grievancePortalUrl: 'https://grievance.municipality.gov.in',
  appName: 'MuniApp',
}

jest.mock('@/lib/api', function() { return { MunicipalityDetail: {} } })

describe('ContactChannels', function() {
  it('renders headquarters address', function() {
    render(React.createElement(ContactChannels, { municipality: mockMunicipality as any }))
    expect(screen.getByText('123 Main St, Chennai')).toBeTruthy()
  })

  it('renders helpline phone', function() {
    render(React.createElement(ContactChannels, { municipality: mockMunicipality as any }))
    expect(screen.getByText('1800-123-4567')).toBeTruthy()
  })

  it('renders email', function() {
    render(React.createElement(ContactChannels, { municipality: mockMunicipality as any }))
    expect(screen.getByText('help@municipality.gov.in')).toBeTruthy()
  })

  it('renders website hostname', function() {
    render(React.createElement(ContactChannels, { municipality: mockMunicipality as any }))
    expect(screen.getByText('municipality.gov.in')).toBeTruthy()
  })

  it('renders grievance portal', function() {
    render(React.createElement(ContactChannels, { municipality: mockMunicipality as any }))
    expect(screen.getByText('File a Complaint')).toBeTruthy()
  })

  it('renders app name', function() {
    render(React.createElement(ContactChannels, { municipality: mockMunicipality as any }))
    expect(screen.getByText('MuniApp')).toBeTruthy()
  })

  it('handles null/empty fields showing Not available', function() {
    var partial = {
      headquartersAddress: null,
      helplinePhone: null,
      email: null,
      websiteUrl: null,
      whatsappNumber: null,
      grievancePortalUrl: null,
      appName: null,
    }
    render(React.createElement(ContactChannels, { municipality: partial as any }))
    var notAvailables = screen.getAllByText('Not available')
    expect(notAvailables.length).toBeGreaterThanOrEqual(6)
    expect(screen.queryByRole('link')).toBeNull()
  })

  it('handles partial fields with some null', function() {
    var partial = {
      headquartersAddress: 'Office',
      helplinePhone: null,
      email: 'test@test.com',
      websiteUrl: null,
      whatsappNumber: null,
      grievancePortalUrl: 'https://grievance.test',
      appName: 'App',
    }
    render(React.createElement(ContactChannels, { municipality: partial as any }))
    expect(screen.getByText('Office')).toBeTruthy()
    expect(screen.getByText('test@test.com')).toBeTruthy()
    expect(screen.getByText('File a Complaint')).toBeTruthy()
    expect(screen.getByText('App')).toBeTruthy()
    // Null fields show 'Not available'
    var notAvail = screen.getAllByText('Not available')
    expect(notAvail.length).toBeGreaterThanOrEqual(1)
  })
})
