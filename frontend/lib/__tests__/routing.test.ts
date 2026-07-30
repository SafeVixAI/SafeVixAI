// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
const mockFetch = jest.fn()
global.fetch = mockFetch

describe('routing', function () {
  beforeEach(function () { mockFetch.mockReset() })

  describe('getRoute', function () {
    it('returns route result on success', async function () {
      mockFetch.mockResolvedValueOnce({ ok: true, json: async function () { return { routes: [{ distance: 5000, duration: 300, geometry: { type: 'LineString', coordinates: [] } }] } } })
      const mod = await import('../routing')
      const result = await mod.getRoute(13, 80, 13.1, 80.1)
      expect(result).not.toBeNull()
      expect(result!.distanceMeters).toBe(5000)
      expect(result!.durationSeconds).toBe(300)
      expect(result!.distanceFormatted).toBe('5.0 km')
    })

    it('returns null on API failure', async function () {
      mockFetch.mockRejectedValueOnce(new Error('fail'))
      const mod = await import('../routing')
      const result = await mod.getRoute(13, 80, 13.1, 80.1)
      expect(result).toBeNull()
    })

    it('returns null on non-ok response', async function () {
      mockFetch.mockResolvedValueOnce({ ok: false })
      const mod = await import('../routing')
      const result = await mod.getRoute(13, 80, 13.1, 80.1)
      expect(result).toBeNull()
    })

    it('returns null when no route', async function () {
      mockFetch.mockResolvedValueOnce({ ok: true, json: async function () { return { routes: [] } } })
      const mod = await import('../routing')
      const result = await mod.getRoute(13, 80, 13.1, 80.1)
      expect(result).toBeNull()
    })

    it('handles route without distance or duration gracefully', async function () {
      mockFetch.mockResolvedValueOnce({ ok: true, json: async function () { return { routes: [{ geometry: { type: 'LineString', coordinates: [] } }] } } })
      const mod = await import('../routing')
      const result = await mod.getRoute(13, 80, 13.1, 80.1)
      expect(result).not.toBeNull()
      expect(result!.distanceMeters).toBe(0)
      expect(result!.durationSeconds).toBe(0)
    })
  })

  describe('addRouteToMap', function () {
    it('adds route layer to map', function () {
      const map = { getLayer: jest.fn().mockReturnValue(null), removeLayer: jest.fn(), getSource: jest.fn().mockReturnValue(null), removeSource: jest.fn(), addSource: jest.fn(), addLayer: jest.fn() }
      const mod = require('../routing')
      mod.addRouteToMap(map, { type: 'LineString', coordinates: [] })
      expect(map.addSource).toHaveBeenCalled()
      expect(map.addLayer).toHaveBeenCalled()
    })

    it('removes existing route before adding', function () {
      const map = { getLayer: jest.fn().mockReturnValue({}), removeLayer: jest.fn(), getSource: jest.fn().mockReturnValue({}), removeSource: jest.fn(), addSource: jest.fn(), addLayer: jest.fn() }
      const mod = require('../routing')
      mod.addRouteToMap(map, { type: 'LineString', coordinates: [] })
      expect(map.removeLayer).toHaveBeenCalled()
      expect(map.removeSource).toHaveBeenCalled()
    })
  })

  describe('removeRouteFromMap', function () {
    it('removes route layers', function () {
      const map = { getLayer: jest.fn().mockReturnValue({}), removeLayer: jest.fn(), getSource: jest.fn().mockReturnValue({}), removeSource: jest.fn() }
      const mod = require('../routing')
      mod.removeRouteFromMap(map)
      expect(map.removeLayer).toHaveBeenCalledWith('route-layer')
      expect(map.removeSource).toHaveBeenCalledWith('route-source')
    })

    it('skips removal when layer and source do not exist', function () {
      const map = { getLayer: jest.fn().mockReturnValue(null), removeLayer: jest.fn(), getSource: jest.fn().mockReturnValue(null), removeSource: jest.fn() }
      const mod = require('../routing')
      mod.removeRouteFromMap(map)
      expect(map.removeLayer).not.toHaveBeenCalled()
      expect(map.removeSource).not.toHaveBeenCalled()
    })
  })

  describe('formatting', function () {
    it('formats distance under 1km', async function () {
      mockFetch.mockResolvedValueOnce({ ok: true, json: async function () { return { routes: [{ distance: 500, duration: 60, geometry: { type: 'LineString', coordinates: [] } }] } } })
      const mod = await import('../routing')
      const result = await mod.getRoute(13, 80, 13.1, 80.1)
      expect(result!.distanceFormatted).toBe('500 m')
    })

    it('formats duration under 60s', async function () {
      mockFetch.mockResolvedValueOnce({ ok: true, json: async function () { return { routes: [{ distance: 100, duration: 30, geometry: { type: 'LineString', coordinates: [] } }] } } })
      const mod = await import('../routing')
      const result = await mod.getRoute(13, 80, 13.1, 80.1)
      expect(result!.durationFormatted).toBe('30 sec')
    })

    it('formats duration in hours and minutes', async function () {
      mockFetch.mockResolvedValueOnce({ ok: true, json: async function () { return { routes: [{ distance: 100000, duration: 7500, geometry: { type: 'LineString', coordinates: [] } }] } } })
      const mod = await import('../routing')
      const result = await mod.getRoute(13, 80, 13.1, 80.1)
      expect(result!.durationFormatted).toBe('2h 5m')
    })
  })
})
