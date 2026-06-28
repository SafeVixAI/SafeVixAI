// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
import React from 'react'
import { render } from '@testing-library/react'
var mockSearchParams = new URLSearchParams()
jest.mock('next/navigation', function() {
  return { useSearchParams: function() { return mockSearchParams }, useRouter: function() { return { push: jest.fn() } }, usePathname: function() { return '/' } }
})
describe('deep-link', function () {
  beforeEach(function() { mockSearchParams = new URLSearchParams() })
  describe('parseDeepLink', function () {
    it('parses lat and lon correctly', async function () {
      var mod = await import('../deep-link')
      var result = mod.parseDeepLink('https://example.com?lat=13.08&lon=80.27')
      expect(result.lat).toBe(13.08)
      expect(result.lon).toBe(80.27)
      expect(result.hasLocation).toBe(true)
    })

    it('returns null for invalid lat', async function () {
      var mod = await import('../deep-link')
      var result = mod.parseDeepLink('https://example.com?lat=999&lon=80.27')
      expect(result.lat).toBeNull()
      expect(result.hasLocation).toBe(false)
    })

    it('returns null for invalid lon', async function () {
      var mod = await import('../deep-link')
      var result = mod.parseDeepLink('https://example.com?lat=13.08&lon=999')
      expect(result.lon).toBeNull()
      expect(result.hasLocation).toBe(false)
    })

    it('parses mode', async function () {
      var mod = await import('../deep-link')
      expect(mod.parseDeepLink('https://example.com?mode=sos').mode).toBe('sos')
      expect(mod.parseDeepLink('https://example.com?mode=track').mode).toBe('track')
      expect(mod.parseDeepLink('https://example.com?mode=report').mode).toBe('report')
      expect(mod.parseDeepLink('https://example.com?mode=locator').mode).toBe('locator')
      expect(mod.parseDeepLink('https://example.com?mode=invalid').mode).toBeNull()
    })

    it('parses source', async function () {
      var mod = await import('../deep-link')
      expect(mod.parseDeepLink('https://example.com?source=share').source).toBe('share')
      expect(mod.parseDeepLink('https://example.com?source=deeplink').source).toBe('deeplink')
      expect(mod.parseDeepLink('https://example.com?source=qr').source).toBe('qr')
      expect(mod.parseDeepLink('https://example.com?source=shortcut').source).toBe('shortcut')
      expect(mod.parseDeepLink('https://example.com?source=unknown').source).toBeNull()
    })

    it('parses state and section', async function () {
      var mod = await import('../deep-link')
      var result = mod.parseDeepLink('https://example.com?state=TN&section=MVA_185')
      expect(result.state).toBe('TN')
      expect(result.section).toBe('MVA_185')
    })

    it('parses sessionId', async function () {
      var mod = await import('../deep-link')
      var result = mod.parseDeepLink('https://example.com?session=abc123')
      expect(result.sessionId).toBe('abc123')
    })

    it('returns nulls for missing params', async function () {
      var mod = await import('../deep-link')
      var result = mod.parseDeepLink('https://example.com')
      expect(result.lat).toBeNull()
      expect(result.lon).toBeNull()
      expect(result.mode).toBeNull()
      expect(result.source).toBeNull()
      expect(result.hasLocation).toBe(false)
    })
  })

  describe('useDeepLinkContext', function () {
    it('parses lat/lon/mode/state/section/source from search params', async function () {
      mockSearchParams.set('lat', '13.08')
      mockSearchParams.set('lon', '80.27')
      mockSearchParams.set('mode', 'sos')
      mockSearchParams.set('state', 'TN')
      mockSearchParams.set('section', 'MVA_185')
      mockSearchParams.set('source', 'share')
      mockSearchParams.set('session', 'abc123')
      var mod = await import('../deep-link')
      var captured
      function TestComp() { captured = mod.useDeepLinkContext(); return null }
      render(React.createElement(TestComp))
      expect(captured.lat).toBe(13.08)
      expect(captured.lon).toBe(80.27)
      expect(captured.mode).toBe('sos')
      expect(captured.state).toBe('TN')
      expect(captured.section).toBe('MVA_185')
      expect(captured.source).toBe('share')
      expect(captured.sessionId).toBe('abc123')
      expect(captured.hasLocation).toBe(true)
    })

    it('returns nulls for missing search params', async function () {
      var mod = await import('../deep-link')
      var captured
      function TestComp() { captured = mod.useDeepLinkContext(); return null }
      render(React.createElement(TestComp))
      expect(captured.lat).toBeNull()
      expect(captured.lon).toBeNull()
      expect(captured.mode).toBeNull()
      expect(captured.source).toBeNull()
      expect(captured.hasLocation).toBe(false)
    })
  })
})
