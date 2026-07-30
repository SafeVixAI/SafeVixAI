jest.mock('@/lib/emergency-numbers', function () {
  return {
    PRIMARY_EMERGENCY_BAR: [
      { id: 'police', service: '112', label: 'Emergency', color: '#FF0000' },
      { id: 'ambulance', service: '108', label: 'Ambulance', color: '#00FF00' },
      { id: 'fire', service: '101', label: 'Fire', color: '#FF6600' },
    ],
  }
})
jest.mock('@/lib/analytics', function () { return { track: { emergencyCallMade: jest.fn() } } })

import { render, screen, fireEvent } from '@testing-library/react'
import React from 'react'
import { EmergencyNumbers } from '../EmergencyNumbers'

describe('EmergencyNumbers', function () {
  it('renders all emergency numbers', function () {
    render(React.createElement(EmergencyNumbers))
    expect(screen.getByText('112')).toBeInTheDocument()
    expect(screen.getByText('108')).toBeInTheDocument()
    expect(screen.getByText('101')).toBeInTheDocument()
  })

  it('renders labels for each number', function () {
    render(React.createElement(EmergencyNumbers))
    expect(screen.getByText('Emergency')).toBeInTheDocument()
    expect(screen.getByText('Ambulance')).toBeInTheDocument()
    expect(screen.getByText('Fire')).toBeInTheDocument()
  })

  it('has nav with correct aria label', function () {
    render(React.createElement(EmergencyNumbers))
    expect(screen.getByLabelText('Emergency phone numbers')).toBeInTheDocument()
  })

  it('renders bar dividers between items', function () {
    const container = render(React.createElement(EmergencyNumbers))
    const dividers = container.container.querySelectorAll('.bar-divider')
    expect(dividers.length).toBe(2)
  })

  it('calls emergencyCallMade analytics on click', function () {
    const analytics = require('@/lib/analytics')
    render(React.createElement(EmergencyNumbers))
    fireEvent.click(screen.getByText('112'))
    expect(analytics.track.emergencyCallMade).toHaveBeenCalledWith('112')
  })

  it('renders tel: hrefs on each anchor', function () {
    render(React.createElement(EmergencyNumbers))
    const links = screen.getAllByRole('link')
    expect(links[0]).toHaveAttribute('href', 'tel:112')
    expect(links[1]).toHaveAttribute('href', 'tel:108')
    expect(links[2]).toHaveAttribute('href', 'tel:101')
  })

  it('renders aria-label with service name and number', function () {
    render(React.createElement(EmergencyNumbers))
    expect(screen.getByLabelText('Call Emergency: 112')).toBeInTheDocument()
    expect(screen.getByLabelText('Call Ambulance: 108')).toBeInTheDocument()
  })
})
