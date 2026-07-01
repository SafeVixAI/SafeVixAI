jest.mock('@/components/ThemeProvider', function() { return { useTheme: function() { return { theme: 'dark' } } } })
jest.mock('@/components/dashboard/TopSearch', function() { return function() { return null } })
jest.mock('@/components/dashboard/SystemHeader', function() { return function() { return null } })
jest.mock('@/lib/store', function() { return { useUserProfile: function() { return { name: 'Test', emergencyContact: '+919999999999' } } } })
jest.mock('@/lib/gsap', function() { return { gsap: { fromTo: jest.fn(), to: jest.fn(), set: jest.fn() } } })
jest.mock('@gsap/react', function() { return { useGSAP: function() {} } })
jest.mock('@/hooks/useSplitTextEntry', function() { return { useSplitTextEntry: function() { return null } } })
jest.mock('@/lib/public-env', function() { return { PUBLIC_API_BASE_URL: '', PUBLIC_CHATBOT_BASE_URL: '' } })
jest.mock('lucide-react', function() { return new Proxy({}, { get: function() { return function() { return null } } }) })
jest.mock('next/dynamic', function() { return function() { return function() { return null } } })

import { render, screen } from '@testing-library/react'
import React from 'react'
import Page from '../app/emergency/page'

describe('EmergencyProtocolsPage', function() {
  it('renders Protocol Terminal heading and tactical labels', function() {
    render(React.createElement(Page))
    expect(screen.getByText('Protocol Terminal')).toBeTruthy()
    expect(screen.getByText('Tactical Center')).toBeTruthy()
    expect(screen.getByText('Satellite Lock')).toBeTruthy()
  })

  it('renders Emergency SOS and CALL 112 NOW', function() {
    render(React.createElement(Page))
    expect(screen.getByText('Emergency SOS')).toBeTruthy()
    expect(screen.getByText('CALL 112 NOW')).toBeTruthy()
  })

  it('renders protocol feed and system labels', function() {
    render(React.createElement(Page))
    expect(screen.getByText('Sentinel V4.2 Protocol Feed')).toBeTruthy()
    expect(screen.getByText('SVA_V4.2_INTEL')).toBeTruthy()
    expect(screen.getByText('OFFLINE READY')).toBeTruthy()
  })

  it('renders quick dial and secure status', function() {
    render(React.createElement(Page))
    expect(screen.getByText('QUICK DIAL: EMERGENCY CONTACT')).toBeTruthy()
    expect(screen.getByText('Armed & Ready')).toBeTruthy()
    expect(screen.getByText('Secure Connection')).toBeTruthy()
  })

  it('renders CPR protocol title', function() {
    render(React.createElement(Page))
    expect(screen.getByText('Cardiopulmonary Resuscitation (CPR)')).toBeTruthy()
  })
})
