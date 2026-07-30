import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'

jest.mock('../../lib/store', function() {
  return {
    useAppStore: jest.fn(function() {
      return {
        userProfile: { name: 'Test User', phone: '+911234567890', bloodGroup: 'O+' },
        gpsLocation: { lat: 13.0827, lon: 80.2707, accuracy: 50 },
        soundsEnabled: false,
      }
    }),
  }
})

jest.mock('../../lib/sos-share', function() {
  return {
    generateSosWhatsAppLink: jest.fn(function() { return Promise.resolve('https://wa.me/911234567890') }),
    generateSosSmsLink: jest.fn(function() { return Promise.resolve('sms:+911234567890') }),
  }
})

jest.mock('../../lib/haptics', function() {
  return { haptics: { sos: jest.fn(), heavy: jest.fn() } }
})

jest.mock('../../lib/sounds', function() {
  return { sounds: { sosSent: jest.fn() } }
})

describe('SOSButton', function() {
  beforeEach(function() {
    jest.clearAllMocks()
  })

  it('renders SOS button', async function() {
    const { SOSButton } = await import('../SOSButton')
    render(React.createElement(SOSButton))
    expect(screen.getByLabelText('Emergency SOS')).toBeInTheDocument()
  })

  it('shows SOS badge text', async function() {
    const { SOSButton } = await import('../SOSButton')
    render(React.createElement(SOSButton))
    expect(screen.getByText('SOS')).toBeInTheDocument()
  })

  it('opens confirmation panel on click', async function() {
    const { SOSButton } = await import('../SOSButton')
    render(React.createElement(SOSButton))
    fireEvent.click(screen.getByLabelText('Emergency SOS'))
    expect(screen.getByText('Confirm SOS Trigger')).toBeInTheDocument()
    expect(screen.getByText('Send WhatsApp SOS')).toBeInTheDocument()
  })

  it('shows Cancel button after expanding', async function() {
    const { SOSButton } = await import('../SOSButton')
    render(React.createElement(SOSButton))
    fireEvent.click(screen.getByLabelText('Emergency SOS'))
    expect(screen.getByText('Cancel')).toBeInTheDocument()
  })

  it('displays GPS coordinates in confirmation', async function() {
    const { SOSButton } = await import('../SOSButton')
    render(React.createElement(SOSButton))
    fireEvent.click(screen.getByLabelText('Emergency SOS'))
    expect(screen.getByText('13.0827, 80.2707')).toBeInTheDocument()
  })

  it('closes panel when Cancel is clicked', async function() {
    const { SOSButton } = await import('../SOSButton')
    render(React.createElement(SOSButton))
    fireEvent.click(screen.getByLabelText('Emergency SOS'))
    expect(screen.getByText('Cancel')).toBeInTheDocument()
    fireEvent.click(screen.getByText('Cancel'))
    expect(screen.queryByText('Confirm SOS Trigger')).not.toBeInTheDocument()
  })

  it('calls window.open for WhatsApp', async function() {
    window.open = jest.fn(function() { return { opener: null, close: jest.fn() } }) as jest.Mock
    const { SOSButton } = await import('../SOSButton')
    render(React.createElement(SOSButton))
    fireEvent.click(screen.getByLabelText('Emergency SOS'))
    fireEvent.click(screen.getByLabelText('Send emergency alert via WhatsApp'))
    await waitFor(function() { expect(window.open).toHaveBeenCalled() })
  })

  it('has SMS alert button', async function() {
    const { SOSButton } = await import('../SOSButton')
    render(React.createElement(SOSButton))
    fireEvent.click(screen.getByLabelText('Emergency SOS'))
    expect(screen.getByLabelText('Send emergency alert via SMS')).toBeInTheDocument()
  })

  it('triggers SMS alert and calls generateSosSmsLink', async function() {
    const sosShare = require('../../lib/sos-share')
    const { SOSButton } = await import('../SOSButton')
    render(React.createElement(SOSButton))
    fireEvent.click(screen.getByLabelText('Emergency SOS'))
    fireEvent.click(screen.getByLabelText('Send emergency alert via SMS'))
    await waitFor(function() { expect(sosShare.generateSosSmsLink).toHaveBeenCalled() })
  })

  it('shows "Acquiring GPS..." when no GPS location', async function() {
    require('../../lib/store').useAppStore.mockImplementation(function() {
      return {
        userProfile: { name: 'Test', phone: '123' },
        gpsLocation: null,
        soundsEnabled: false,
      }
    })
    const { SOSButton } = await import('../SOSButton')
    render(React.createElement(SOSButton))
    fireEvent.click(screen.getByLabelText('Emergency SOS'))
    expect(screen.getByText('Acquiring GPS...')).toBeInTheDocument()
  })

  it('plays sound when soundsEnabled is true', async function() {
    require('../../lib/store').useAppStore.mockImplementation(function() {
      return {
        userProfile: { name: 'Test', phone: '123' },
        gpsLocation: { lat: 10, lon: 20, accuracy: 50 },
        soundsEnabled: true,
      }
    })
    const sounds = require('../../lib/sounds')
    const { SOSButton } = await import('../SOSButton')
    window.open = jest.fn(function() { return null }) as jest.Mock
    render(React.createElement(SOSButton))
    fireEvent.click(screen.getByLabelText('Emergency SOS'))
    fireEvent.click(screen.getByLabelText('Send emergency alert via WhatsApp'))
    await waitFor(function() { expect(sounds.sounds.sosSent).toHaveBeenCalled() })
  })

  it('sets popup.opener to null when popup exists', async function() {
    const popup = { opener: null, close: jest.fn() }
    window.open = jest.fn(function() { return popup }) as jest.Mock
    const { SOSButton } = await import('../SOSButton')
    render(React.createElement(SOSButton))
    fireEvent.click(screen.getByLabelText('Emergency SOS'))
    fireEvent.click(screen.getByLabelText('Send emergency alert via WhatsApp'))
    await waitFor(function() { expect(popup.opener).toBeNull() })
  })

  it('closes panel when SOS button clicked again', async function() {
    const { SOSButton } = await import('../SOSButton')
    render(React.createElement(SOSButton))
    fireEvent.click(screen.getByLabelText('Emergency SOS'))
    expect(screen.getByText('Confirm SOS Trigger')).toBeInTheDocument()
    fireEvent.click(screen.getByLabelText('Emergency SOS'))
    expect(screen.queryByText('Confirm SOS Trigger')).not.toBeInTheDocument()
  })
})
