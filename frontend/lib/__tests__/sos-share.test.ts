// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
jest.mock('../reverse-geocode', function () { return { getAddressFromGPS: jest.fn() } })
jest.mock('../safety-constants', function () { return { AMBULANCE_NUMBER: '108', EMERGENCY_NUMBER: '112', W3W_LOOKUP_TIMEOUT_MS: 3000 } })

var mockFetch = jest.fn()
global.fetch = mockFetch

describe('sos-share', function () {
  var mockProfile = { name: 'John', bloodGroup: 'O+', vehicleNumber: 'TN01AB1234' }
  var mockLocation = { lat: 13.0827, lon: 80.2707 }

  beforeEach(function () {
    mockFetch.mockReset()
  })

  function decodeUri(s: string) { return decodeURIComponent(s) }

  describe('generateSosWhatsAppLinkSync', function () {
    it('generates link with full profile', async function () {
      var mod = await import('../sos-share')
      var link = mod.generateSosWhatsAppLinkSync(mockProfile, mockLocation)
      var decoded = decodeUri(link)
      expect(decoded).toContain('wa.me')
      expect(decoded).toContain('John')
      expect(decoded).toContain('O+')
      expect(decoded).toContain('google.com/maps')
    })

    it('handles null profile and location', async function () {
      var mod = await import('../sos-share')
      var link = mod.generateSosWhatsAppLinkSync(null, null)
      var decoded = decodeUri(link)
      expect(decoded).toContain('Anonymous')
      expect(decoded).toContain('Not Specified')
    })
  })

  describe('generateSosSmsLink', function () {
    it('generates SMS link', async function () {
      var mod = await import('../sos-share')
      var link = mod.generateSosSmsLink(mockProfile, mockLocation)
      expect(link).toContain('sms:112')
      expect(link).toContain('John')
    })

    it('handles null inputs', async function () {
      var mod = await import('../sos-share')
      var link = mod.generateSosSmsLink(null, null)
      expect(link).toContain('sms:112')
      expect(link).toContain('User')
    })
  })

  describe('generateSosWhatsAppLink', function () {
    it('generates link with address lookup', async function () {
      var reverseGeocode = require('../reverse-geocode')
      reverseGeocode.getAddressFromGPS.mockResolvedValue({ displayAddress: 'Chennai' })
      mockFetch.mockResolvedValueOnce({ ok: true, json: async function () { return { words: 'filled.verb.ship' } } })
      var mod = await import('../sos-share')
      var link = await mod.generateSosWhatsAppLink(mockProfile, mockLocation)
      expect(link).toContain('Chennai')
    })

    it('handles null location', async function () {
      var mod = await import('../sos-share')
      var link = await mod.generateSosWhatsAppLink(mockProfile, null)
      var decoded = decodeUri(link)
      expect(decoded).toContain('GPS Signal Lost')
    })

    it('handles w3w fetch failure gracefully', async function () {
      var reverseGeocode = require('../reverse-geocode')
      reverseGeocode.getAddressFromGPS.mockResolvedValue({ displayAddress: 'Chennai' })
      mockFetch.mockRejectedValueOnce(new Error('w3w down'))
      var mod = await import('../sos-share')
      var link = await mod.generateSosWhatsAppLink(mockProfile, mockLocation)
      expect(link).toContain('Chennai')
    })

    it('handles w3w non-ok response', async function () {
      var reverseGeocode = require('../reverse-geocode')
      reverseGeocode.getAddressFromGPS.mockResolvedValue({ displayAddress: 'Chennai' })
      mockFetch.mockResolvedValueOnce({ ok: false })
      var mod = await import('../sos-share')
      var link = await mod.generateSosWhatsAppLink(mockProfile, mockLocation)
      expect(link).toContain('Chennai')
    })

    it('handles w3w non-string words', async function () {
      var reverseGeocode = require('../reverse-geocode')
      reverseGeocode.getAddressFromGPS.mockResolvedValue({ displayAddress: 'Chennai' })
      mockFetch.mockResolvedValueOnce({ ok: true, json: async function () { return { words: 12345 } } })
      var mod = await import('../sos-share')
      var link = await mod.generateSosWhatsAppLink(mockProfile, mockLocation)
      expect(link).toContain('Chennai')
    })

    it('handles null profile in async link', async function () {
      var mod = await import('../sos-share')
      var link = await mod.generateSosWhatsAppLink(null, mockLocation)
      var decoded = decodeUri(link)
      expect(decoded).toContain('Anonymous User')
    })
  })
})
