// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
const mockFetch = jest.fn()
global.fetch = mockFetch

describe('india-locations', function () {
  beforeEach(function () {
    mockFetch.mockReset()
    jest.resetModules()
  })

  describe('getIndianStates', function () {
    it('returns states on successful API call', async function () {
      mockFetch.mockResolvedValueOnce({ ok: true, json: async function () { return { data: { states: [{ name: 'Tamil Nadu' }, { name: 'Kerala' }] } } } })
      const mod = await import('../india-locations')
      const states = await mod.getIndianStates()
      expect(states).toEqual(['Kerala', 'Tamil Nadu'])
    })

    it('returns fallback states on API failure', async function () {
      mockFetch.mockRejectedValueOnce(new Error('Network error'))
      const mod = await import('../india-locations')
      const states = await mod.getIndianStates()
      expect(states.length).toBeGreaterThanOrEqual(2)
    })

    it('returns fallback states on non-ok response', async function () {
      mockFetch.mockResolvedValueOnce({ ok: false })
      const mod = await import('../india-locations')
      const states = await mod.getIndianStates()
      expect(states.length).toBeGreaterThanOrEqual(2)
    })

    it('caches states after first call', async function () {
      mockFetch.mockResolvedValueOnce({ ok: true, json: async function () { return { data: { states: [{ name: 'Goa' }] } } } })
      const mod = await import('../india-locations')
      await mod.getIndianStates()
      mockFetch.mockClear()
      const states = await mod.getIndianStates()
      expect(states).toEqual(['Goa'])
      expect(mockFetch).not.toHaveBeenCalled()
    })
  })

  describe('getCitiesForState', function () {
    it('returns cities on success', async function () {
      mockFetch.mockResolvedValueOnce({ ok: true, json: async function () { return { data: ['Chennai', 'Coimbatore'] } } })
      const mod = await import('../india-locations')
      const cities = await mod.getCitiesForState('Tamil Nadu')
      expect(cities).toEqual(['Chennai', 'Coimbatore'])
    })

    it('returns empty array on failure', async function () {
      mockFetch.mockRejectedValueOnce(new Error('fail'))
      const mod = await import('../india-locations')
      const cities = await mod.getCitiesForState('Unknown')
      expect(cities).toEqual([])
    })

    it('returns cached cities on second call', async function () {
      mockFetch.mockResolvedValueOnce({ ok: true, json: async function () { return { data: ['Chennai', 'Coimbatore'] } } })
      const mod = await import('../india-locations')
      await mod.getCitiesForState('Tamil Nadu')
      mockFetch.mockClear()
      const cities = await mod.getCitiesForState('Tamil Nadu')
      expect(cities).toEqual(['Chennai', 'Coimbatore'])
      expect(mockFetch).not.toHaveBeenCalled()
    })

    it('returns empty array on non-ok response', async function () {
      mockFetch.mockResolvedValueOnce({ ok: false })
      const mod = await import('../india-locations')
      const cities = await mod.getCitiesForState('Tamil Nadu')
      expect(cities).toEqual([])
    })

    it('sorts empty array when data is null', async function () {
      mockFetch.mockResolvedValueOnce({ ok: true, json: async function () { return { data: null } } })
      const mod = await import('../india-locations')
      const cities = await mod.getCitiesForState('Tamil Nadu')
      expect(cities).toEqual([])
    })
  })

  describe('getIndianStates fallback', function () {
    it('returns fallback states when API returns null states', async function () {
      mockFetch.mockResolvedValueOnce({ ok: true, json: async function () { return { data: { states: null } } } })
      const mod = await import('../india-locations')
      const states = await mod.getIndianStates()
      expect(states.length).toBeGreaterThanOrEqual(2)
    })

    it('returns fallback states when API returns empty states', async function () {
      mockFetch.mockResolvedValueOnce({ ok: true, json: async function () { return { data: { states: [] } } } })
      const mod = await import('../india-locations')
      const states = await mod.getIndianStates()
      expect(states.length).toBeGreaterThanOrEqual(2)
    })
  })
})
