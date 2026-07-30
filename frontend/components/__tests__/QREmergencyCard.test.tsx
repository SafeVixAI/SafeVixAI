// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

if (typeof global.TextEncoder === 'undefined') {
  const util = require('util')
  global.TextEncoder = util.TextEncoder
}

jest.mock('@/lib/analytics', function() { return { track: { qrCardAction: jest.fn() } } })
jest.mock('qrcode.react', function() {
  const React = require('react')
  return {
    QRCodeSVG: function() {
      return React.createElement('div', { 'data-testid': 'qr-code' }, 'QR')
    },
    __esModule: true,
    default: { QRCodeSVG: function() { return React.createElement('div', null, 'QR') } },
  }
})

import { render, screen, fireEvent, act } from '@testing-library/react'
import React from 'react'
import QREmergencyCard from '../profile/QREmergencyCard'
import { useAppStore } from '@/lib/store'
const track = require('@/lib/analytics').track

describe('QREmergencyCard', function() {
  beforeEach(function() {
    useAppStore.setState({
      userProfile: {
        id: 'test-1',
        name: 'Test User',
        phone: '+911234567890',
        bloodGroup: 'O+',
        vehicleNumber: 'TN01AB1234',
        emergencyContact: '+919876543210',
        emergencyContacts: [],
        medicalConditions: '',
        preferredLanguage: 'en',
      },
    })
    jest.clearAllMocks()
  })

  it('renders QR code section', function() {
    render(React.createElement(QREmergencyCard))
    expect(screen.getByText('QR Emergency Card')).toBeTruthy()
  })

  it('shows Card Ready badge when profile complete', function() {
    render(React.createElement(QREmergencyCard))
    expect(screen.getByText('Card Ready')).toBeTruthy()
  })

  it('renders preview button', function() {
    render(React.createElement(QREmergencyCard))
    expect(screen.getByText('Preview')).toBeTruthy()
  })

  it('renders share button', function() {
    render(React.createElement(QREmergencyCard))
    expect(screen.getByText('Share Card')).toBeTruthy()
  })

  it('shows Incomplete badge when profile missing blood group', function() {
    useAppStore.setState({ userProfile: { id: '', name: '', phone: '', bloodGroup: '', vehicleNumber: '', emergencyContact: '', emergencyContacts: [], medicalConditions: '', preferredLanguage: 'en' } })
    render(React.createElement(QREmergencyCard))
    expect(screen.getByText('Incomplete')).toBeTruthy()
  })

  it('shows warning text when profile incomplete', function() {
    useAppStore.setState({ userProfile: { id: '', name: '', phone: '', bloodGroup: '', vehicleNumber: '', emergencyContact: '', emergencyContacts: [], medicalConditions: '', preferredLanguage: 'en' } })
    render(React.createElement(QREmergencyCard))
    expect(screen.getByText(/first responders need blood group/i)).toBeTruthy()
  })

  it('shows fallback display ID when no name', function() {
    useAppStore.setState({ userProfile: { id: '', name: '', phone: '', bloodGroup: 'O+', vehicleNumber: '', emergencyContact: '+91', emergencyContacts: [], medicalConditions: '', preferredLanguage: 'en' } })
    render(React.createElement(QREmergencyCard))
    expect(screen.getByText('SVA-XXXX-X')).toBeTruthy()
  })

  it('shows display ID derived from name', function() {
    useAppStore.setState({ userProfile: { id: '', name: 'John Doe', phone: '', bloodGroup: 'O+', vehicleNumber: '', emergencyContact: '+91', emergencyContacts: [], medicalConditions: '', preferredLanguage: 'en' } })
    render(React.createElement(QREmergencyCard))
    expect(screen.getByText('SVA-JOHN-X')).toBeTruthy()
  })

  it('shows Unknown when operator name empty in preview modal', function() {
    useAppStore.setState({ userProfile: { id: '', name: '', phone: '', bloodGroup: 'O+', vehicleNumber: '', emergencyContact: '+91', emergencyContacts: [], medicalConditions: '', preferredLanguage: 'en' } })
    render(React.createElement(QREmergencyCard))
    fireEvent.click(screen.getByText('Preview'))
    expect(screen.getByText('UNKNOWN OPERATOR')).toBeTruthy()
  })

  it('shows Not set for missing blood group', function() {
    useAppStore.setState({ userProfile: { id: '', name: 'Test', phone: '', bloodGroup: '', vehicleNumber: '', emergencyContact: '', emergencyContacts: [], medicalConditions: '', preferredLanguage: 'en' } })
    render(React.createElement(QREmergencyCard))
    expect(screen.getAllByText('Not set').length).toBeGreaterThan(0)
  })

  it('copies link to clipboard on share when navigator.share unavailable', async function() {
    const writeText = jest.fn().mockResolvedValue(undefined)
    Object.assign(navigator, { clipboard: { writeText } })
    render(React.createElement(QREmergencyCard))
    const shareBtn = screen.getByText('Share Card')
    await act(async function() { fireEvent.click(shareBtn) })
    expect(track.qrCardAction).toHaveBeenCalledWith('share')
    expect(writeText).toHaveBeenCalled()
  })

  it('shows Copied state after copying', async function() {
    const writeText = jest.fn().mockResolvedValue(undefined)
    Object.assign(navigator, { clipboard: { writeText } })
    render(React.createElement(QREmergencyCard))
    const shareBtn = screen.getByText('Share Card')
    await act(async function() { fireEvent.click(shareBtn) })
    expect(screen.getByText('Copied!')).toBeTruthy()
  })

  it('calls navigator.share when available', async function() {
    const shareMock = jest.fn().mockResolvedValue(undefined)
    Object.assign(navigator, { share: shareMock, clipboard: { writeText: jest.fn() } })
    render(React.createElement(QREmergencyCard))
    const shareBtn = screen.getByText('Share Card')
    await act(async function() { fireEvent.click(shareBtn) })
    expect(shareMock).toHaveBeenCalled()
    expect(shareMock.mock.calls[0][0].title).toBe('SafeVixAI Emergency Card')
  })

  it('opens preview modal on Preview button click', function() {
    render(React.createElement(QREmergencyCard))
    const previewBtn = screen.getByText('Preview')
    fireEvent.click(previewBtn)
    expect(track.qrCardAction).toHaveBeenCalledWith('preview')
    expect(screen.getByRole('dialog')).toBeTruthy()
  })

  it('preview modal shows operator name', function() {
    render(React.createElement(QREmergencyCard))
    fireEvent.click(screen.getByText('Preview'))
    expect(screen.getByText('Test User')).toBeTruthy()
  })

  it('preview modal shows display ID from profile', function() {
    render(React.createElement(QREmergencyCard))
    fireEvent.click(screen.getByText('Preview'))
    const idEls = screen.getAllByText('test-1')
    expect(idEls.length).toBeGreaterThanOrEqual(2)
  })

  it('preview modal shows blood group', function() {
    render(React.createElement(QREmergencyCard))
    fireEvent.click(screen.getByText('Preview'))
    expect(screen.getAllByText('O+').length).toBeGreaterThan(0)
  })

  it('preview modal share button calls navigator.share', async function() {
    const shareMock = jest.fn().mockResolvedValue(undefined)
    Object.assign(navigator, { share: shareMock })
    render(React.createElement(QREmergencyCard))
    fireEvent.click(screen.getByText('Preview'))
    const shareBtns = screen.getAllByText('Share')
    await act(async function() { fireEvent.click(shareBtns[shareBtns.length - 1]) })
    expect(shareMock).toHaveBeenCalled()
  })

  it('preview modal closes on Close button click', function() {
    render(React.createElement(QREmergencyCard))
    fireEvent.click(screen.getByText('Preview'))
    expect(screen.getByRole('dialog')).toBeTruthy()
    fireEvent.click(screen.getByText('Close'))
    expect(screen.queryByRole('dialog')).toBeNull()
  })

  it('preview modal closes on backdrop click', function() {
    render(React.createElement(QREmergencyCard))
    fireEvent.click(screen.getByText('Preview'))
    const backdrop = document.querySelector('.fixed.inset-0')
    expect(backdrop).toBeTruthy()
    fireEvent.click(backdrop!)
    expect(screen.queryByRole('dialog')).toBeNull()
  })

  it('preview modal closes on Escape key', function() {
    render(React.createElement(QREmergencyCard))
    fireEvent.click(screen.getByText('Preview'))
    expect(screen.getByRole('dialog')).toBeTruthy()
    fireEvent.keyDown(document, { key: 'Escape' })
    expect(screen.queryByRole('dialog')).toBeNull()
  })

  it('traps Tab focus cycling forward in preview modal', function() {
    render(React.createElement(QREmergencyCard))
    fireEvent.click(screen.getByText('Preview'))
    const dialog = screen.getByRole('dialog')
    const buttons = dialog.querySelectorAll('button')
    const firstBtn = buttons[0]
    const lastBtn = buttons[buttons.length - 1]
    jest.spyOn(firstBtn, 'focus')
    jest.spyOn(lastBtn, 'focus')
    lastBtn.focus()
    fireEvent.keyDown(document, { key: 'Tab', shiftKey: false })
    expect(firstBtn.focus).toHaveBeenCalled()
  })

  it('traps Shift+Tab focus cycling backward in preview modal', function() {
    render(React.createElement(QREmergencyCard))
    fireEvent.click(screen.getByText('Preview'))
    const dialog = screen.getByRole('dialog')
    const buttons = dialog.querySelectorAll('button')
    const firstBtn = buttons[0]
    const lastBtn = buttons[buttons.length - 1]
    jest.spyOn(firstBtn, 'focus')
    jest.spyOn(lastBtn, 'focus')
    firstBtn.focus()
    fireEvent.keyDown(document, { key: 'Tab', shiftKey: true })
    expect(lastBtn.focus).toHaveBeenCalled()
  })

  it('does not cycle focus on non-Tab key in preview modal', function() {
    render(React.createElement(QREmergencyCard))
    fireEvent.click(screen.getByText('Preview'))
    const dialog = screen.getByRole('dialog')
    const buttons = dialog.querySelectorAll('button')
    const firstBtn = buttons[0]
    jest.spyOn(firstBtn, 'focus')
    fireEvent.keyDown(document, { key: 'a' })
    expect(firstBtn.focus).not.toHaveBeenCalled()
  })

  it('no-op when dialog ref is null', function() {
    render(React.createElement(QREmergencyCard))
    fireEvent.click(screen.getByText('Preview'))
    expect(screen.getByRole('dialog')).toBeTruthy()
    fireEvent.keyDown(document, { key: 'Tab', shiftKey: false })
  })
})
