// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
var mockFetch = jest.fn()
global.fetch = mockFetch

describe('geocoding', function () {
  beforeEach(function () {
    mockFetch.mockReset()
  })

  it('searchPlaces returns empty for short queries', async function () {
    var mod = await import('../geocoding')
    var results = await mod.searchPlaces('', 5)
    expect(results).toEqual([])
  })

  it('searchPlaces returns empty for whitespace-only query', async function () {
    var mod = await import('../geocoding')
    var results = await mod.searchPlaces('   ', 5)
    expect(results).toEqual([])
  })

  it('searchPlaces returns empty when fetch fails', async function () {
    mockFetch.mockResolvedValueOnce({ ok: false })
    var mod = await import('../geocoding')
    var results = await mod.searchPlaces('Chennai')
    expect(results).toEqual([])
  })

  it('searchPlaces parses Photon features correctly', async function () {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async function () {
        return {
          features: [
            {
              properties: { name: 'Chennai', city: 'Chennai', state: 'Tamil Nadu', country: 'India' },
              geometry: { coordinates: [80.27, 13.08] },
            },
          ],
        }
      },
    })
    var mod = await import('../geocoding')
    var results = await mod.searchPlaces('Chennai')
    expect(results).toHaveLength(1)
    expect(results[0].name).toBe('Chennai')
    expect(results[0].lat).toBe(13.08)
    expect(results[0].lon).toBe(80.27)
    expect(results[0].label).toBe('Chennai, Chennai, Tamil Nadu')
  })

  it('searchPlaces returns empty on fetch error', async function () {
    mockFetch.mockRejectedValueOnce(new Error('network error'))
    var mod = await import('../geocoding')
    var results = await mod.searchPlaces('Chennai')
    expect(results).toEqual([])
  })

  it('searchPlaces handles null features in response', async function () {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async function () { return { features: null } },
    })
    var mod = await import('../geocoding')
    var results = await mod.searchPlaces('Chennai')
    expect(results).toEqual([])
  })

  it('searchPlaces handles empty features array', async function () {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async function () { return { features: [] } },
    })
    var mod = await import('../geocoding')
    var results = await mod.searchPlaces('Chennai')
    expect(results).toEqual([])
  })

  it('searchPlaces uses county fallback when city is missing', async function () {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async function () {
        return {
          features: [{
            properties: { name: 'Test', county: 'Test County', state: 'Test State', country: 'India' },
            geometry: { coordinates: [80.27, 13.08] },
          }],
        }
      },
    })
    var mod = await import('../geocoding')
    var results = await mod.searchPlaces('Chennai')
    expect(results[0].city).toBe('Test County')
    expect(results[0].label).toBe('Test, Test County, Test State')
  })

  it('searchPlaces handles missing properties/geometry', async function () {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async function () {
        return {
          features: [
            {},
          ],
        }
      },
    })
    var mod = await import('../geocoding')
    var results = await mod.searchPlaces('test')
    expect(results).toHaveLength(1)
    expect(results[0].name).toBe('')
  })

  it('createDebouncedSearch calls callback after delay', async function () {
    jest.useFakeTimers()
    mockFetch.mockResolvedValue({
      ok: true,
      json: async function () { return { features: [] } },
    })
    var mod = await import('../geocoding')
    var debounced = mod.createDebouncedSearch(300)
    var callback = jest.fn()
    debounced('Chennai', callback)
    expect(callback).not.toHaveBeenCalled()
    await jest.runAllTimersAsync()
    expect(callback).toHaveBeenCalledTimes(1)
    jest.useRealTimers()
  })

  it('createDebouncedSearch cancels previous timer', async function () {
    jest.useFakeTimers()
    mockFetch.mockResolvedValue({
      ok: true,
      json: async function () { return { features: [] } },
    })
    var mod = await import('../geocoding')
    var debounced = mod.createDebouncedSearch(300)
    var callback = jest.fn()
    debounced('Chennai', callback)
    debounced('Mumbai', callback)
    await jest.runAllTimersAsync()
    expect(callback).toHaveBeenCalledTimes(1)
    jest.useRealTimers()
  })
})
