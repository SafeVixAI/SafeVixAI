// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
jest.mock('../reverse-geocode', function () { return { getAddressFromGPS: jest.fn() } })
jest.mock('../safety-constants', function () { return { AMBULANCE_NUMBER: '108', EMERGENCY_NUMBER: '112', W3W_LOOKUP_TIMEOUT_MS: 3000 } })

const mockFetch = jest.fn()
global.fetch = mockFetch

describe('sos-share', function () {
  const mockProfile = { name: 'John', bloodGroup: 'O+', vehicleNumber: 'TN01AB1234' }
  const mockLocation = { lat: 13.0827, lon: 80.2707 }

  beforeEach(function () {
    mockFetch.mockReset()
  })

  function decodeUri(s: string) { return decodeURIComponent(s) }

  describe('generateSosWhatsAppLinkSync', function () {
    it('generates link with full profile', async function () {
      const mod = await import('../sos-share')
      const link = mod.generateSosWhatsAppLinkSync(mockProfile, mockLocation)
      const decoded = decodeUri(link)
      expect(decoded).toContain('wa.me')
      expect(decoded).toContain('John')
      expect(decoded).toContain('O+')
      expect(decoded).toContain('google.com/maps')
    })

    it('handles null profile and location', async function () {
      const mod = await import('../sos-share')
      const link = mod.generateSosWhatsAppLinkSync(null, null)
      const decoded = decodeUri(link)
      expect(decoded).toContain('Anonymous')
      expect(decoded).toContain('Not Specified')
    })
  })

  describe('generateSosSmsLink', function () {
    it('generates SMS link', async function () {
      const mod = await import('../sos-share')
      const link = mod.generateSosSmsLink(mockProfile, mockLocation)
      expect(link).toContain('sms:112')
      expect(link).toContain('John')
    })

    it('handles null inputs', async function () {
      const mod = await import('../sos-share')
      const link = mod.generateSosSmsLink(null, null)
      expect(link).toContain('sms:112')
      expect(link).toContain('User')
    })
  })

  describe('generateSosWhatsAppLink', function () {
    it('generates link with address lookup', async function () {
      const reverseGeocode = require('../reverse-geocode')
      reverseGeocode.getAddressFromGPS.mockResolvedValue({ displayAddress: 'Chennai' })
      mockFetch.mockResolvedValueOnce({ ok: true, json: async function () { return { words: 'filled.verb.ship' } } })
      const mod = await import('../sos-share')
      const link = await mod.generateSosWhatsAppLink(mockProfile, mockLocation)
      expect(link).toContain('Chennai')
    })

    it('handles null location', async function () {
      const mod = await import('../sos-share')
      const link = await mod.generateSosWhatsAppLink(mockProfile, null)
      const decoded = decodeUri(link)
      expect(decoded).toContain('GPS Signal Lost')
    })

    it('handles w3w fetch failure gracefully', async function () {
      const reverseGeocode = require('../reverse-geocode')
      reverseGeocode.getAddressFromGPS.mockResolvedValue({ displayAddress: 'Chennai' })
      mockFetch.mockRejectedValueOnce(new Error('w3w down'))
      const mod = await import('../sos-share')
      const link = await mod.generateSosWhatsAppLink(mockProfile, mockLocation)
      expect(link).toContain('Chennai')
    })

    it('handles w3w non-ok response', async function () {
      const reverseGeocode = require('../reverse-geocode')
      reverseGeocode.getAddressFromGPS.mockResolvedValue({ displayAddress: 'Chennai' })
      mockFetch.mockResolvedValueOnce({ ok: false })
      const mod = await import('../sos-share')
      const link = await mod.generateSosWhatsAppLink(mockProfile, mockLocation)
      expect(link).toContain('Chennai')
    })

    it('handles w3w non-string words', async function () {
      const reverseGeocode = require('../reverse-geocode')
      reverseGeocode.getAddressFromGPS.mockResolvedValue({ displayAddress: 'Chennai' })
      mockFetch.mockResolvedValueOnce({ ok: true, json: async function () { return { words: 12345 } } })
      const mod = await import('../sos-share')
      const link = await mod.generateSosWhatsAppLink(mockProfile, mockLocation)
      expect(link).toContain('Chennai')
    })

    it('handles null profile in async link', async function () {
      const mod = await import('../sos-share')
      const link = await mod.generateSosWhatsAppLink(null, mockLocation)
      const decoded = decodeUri(link)
      expect(decoded).toContain('Anonymous User')
    })
  })
})
