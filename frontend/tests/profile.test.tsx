jest.mock('next/navigation', function() {
  return { useRouter: function() { return { push: jest.fn() } }, usePathname: function() { return '/profile' }, useSearchParams: function() { return new URLSearchParams() } }
})
jest.mock('next/link', function() {
  return function Link({ children }: { children: React.ReactNode }) { return children }
})
jest.mock('@/lib/gsap', function() {
  return { gsap: { fromTo: jest.fn(), to: jest.fn(), globalTimeline: { timeScale: jest.fn() }, killTweensOf: jest.fn() }, default: { fromTo: jest.fn(), to: jest.fn() } }
})
jest.mock('@gsap/react', function() { return { useGSAP: function() {} } })
jest.mock('@/lib/analytics', function() { return { track: { profileCompleted: jest.fn() } } })
jest.mock('sonner', function() { return { toast: { error: jest.fn(), success: jest.fn() } } })
jest.mock('@/lib/guest-auth', function() {
  return { getOrCreateGuestId: function() { return 'guest-1' }, getGuestProfile: function() { return null }, updateGuestProfile: jest.fn(), isGuestMode: function() { return true } }
})
jest.mock('@/components/dashboard/TopSearch', function() { return function() { return null } })
jest.mock('@/components/ui/TerminalHeader', function() { return { TerminalHeader: function() { return null } } })
jest.mock('@/components/ui/SurfaceCard', function() { return { SurfaceCard: function({ children, padding, className }) { const React = require('react'); return React.createElement('div', { className }, children) } } })
jest.mock('@/components/ui/SettingRow', function() { return { SettingRow: function({ icon, title, description, rightElement }) { const React = require('react'); return React.createElement('div', null, title, rightElement) } } })
jest.mock('@/components/dashboard/Toggle', function() { return function() { return null } })
jest.mock('@/components/profile/QREmergencyCard', function() { return function() { return null } })
jest.mock('lucide-react', function() { return new Proxy({}, { get: function() { return function() { return null } } }) })

import { render, screen, fireEvent, act } from '@testing-library/react'
import React from 'react'
import ProfilePage from '../app/profile/page'
import { useAppStore } from '@/lib/store'

describe('Profile Page', function() {
  beforeEach(function() {
    useAppStore.setState({
      userProfile: { name: 'TestUser', bloodGroup: 'O+', vehicleNumber: 'TN01AB1234', emergencyContact: '+919876543210', emergencyContacts: [], medicalConditions: '', preferredLanguage: 'en', id: 'test-1', phone: '+911234567890' },
      crashDetectionEnabled: false,
      isAuthenticated: true,
    })
  })

  it('renders profile page sr-only heading', function() {
    render(React.createElement(ProfilePage))
    expect(screen.getByText('User Profile')).toBeTruthy()
  })

  it('renders user name', function() {
    render(React.createElement(ProfilePage))
    expect(screen.getByText('TestUser')).toBeTruthy()
  })

  it('renders blood group', function() {
    render(React.createElement(ProfilePage))
    expect(screen.getByText('O+')).toBeTruthy()
  })

  it('renders vehicle number', function() {
    render(React.createElement(ProfilePage))
    expect(screen.getByText('TN01AB1234')).toBeTruthy()
  })

  it('renders emergency contact', function() {
    render(React.createElement(ProfilePage))
    expect(screen.getByText('+919876543210')).toBeTruthy()
  })

  it('renders Edit Profile button', function() {
    render(React.createElement(ProfilePage))
    expect(screen.getByText('Edit Profile')).toBeTruthy()
  })

  it('renders Crash Detection toggle', function() {
    render(React.createElement(ProfilePage))
    expect(screen.getByText('Crash Detection')).toBeTruthy()
  })

  it('renders V8 Offline Mode toggle', function() {
    render(React.createElement(ProfilePage))
    expect(screen.getByText('V8 Offline Mode')).toBeTruthy()
  })

  it('renders Push Hub toggle', function() {
    render(React.createElement(ProfilePage))
    expect(screen.getByText('Push Hub')).toBeTruthy()
  })

  it('renders Sign Out Operator button when authenticated', function() {
    render(React.createElement(ProfilePage))
    expect(screen.getByText('Sign Out Operator')).toBeTruthy()
  })

  it('renders PURGE LOCAL SESSION button', function() {
    render(React.createElement(ProfilePage))
    expect(screen.getByText('PURGE LOCAL SESSION')).toBeTruthy()
  })

  it('renders Mission Protocol section heading', function() {
    render(React.createElement(ProfilePage))
    expect(screen.getByText('Mission Protocol')).toBeTruthy()
  })

  it('renders display ID tag', function() {
    render(React.createElement(ProfilePage))
    expect(screen.getByText(/test-1/)).toBeTruthy()
  })

  it('renders Profile Matrix Sync badge', function() {
    render(React.createElement(ProfilePage))
    expect(screen.getByText('Profile Matrix Sync')).toBeTruthy()
  })

  it('renders VEHICLE_REGISTRATION label', function() {
    render(React.createElement(ProfilePage))
    expect(screen.getByText('VEHICLE_REGISTRATION')).toBeTruthy()
  })

  it('enters edit mode on Edit Profile click', function() {
    render(React.createElement(ProfilePage))
    act(function() { fireEvent.click(screen.getByText('Edit Profile')) })
    expect(screen.getByText('Cancel')).toBeTruthy()
    expect(screen.getByText('Save')).toBeTruthy()
  })

  it('cancel edit returns to view mode', function() {
    render(React.createElement(ProfilePage))
    act(function() { fireEvent.click(screen.getByText('Edit Profile')) })
    act(function() { fireEvent.click(screen.getByText('Cancel')) })
    expect(screen.getByText('Edit Profile')).toBeTruthy()
  })

  it('save flashes Profile Saved banner', function() {
    render(React.createElement(ProfilePage))
    act(function() { fireEvent.click(screen.getByText('Edit Profile')) })
    act(function() { fireEvent.click(screen.getByText('Save')) })
    expect(screen.getByText('Profile Saved')).toBeTruthy()
  })

  it('shows Full Name input in edit mode', function() {
    render(React.createElement(ProfilePage))
    act(function() { fireEvent.click(screen.getByText('Edit Profile')) })
    expect(screen.getByLabelText('Full Name')).toBeTruthy()
  })

  it('shows Vehicle Number input in edit mode', function() {
    render(React.createElement(ProfilePage))
    act(function() { fireEvent.click(screen.getByText('Edit Profile')) })
    expect(screen.getByLabelText('Vehicle Number')).toBeTruthy()
  })

  it('shows Blood Group select in edit mode', function() {
    render(React.createElement(ProfilePage))
    act(function() { fireEvent.click(screen.getByText('Edit Profile')) })
    expect(screen.getByLabelText('Blood Group')).toBeTruthy()
  })
})
