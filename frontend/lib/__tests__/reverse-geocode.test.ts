// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
const mockFetch = jest.fn()
global.fetch = mockFetch

describe('reverse-geocode', function () {
  beforeEach(function () {
    mockFetch.mockReset()
  })

  it('getAddressFromGPS returns parsed address on success', async function () {
    mockFetch.mockResolvedValueOnce({ ok: true, json: async function () { return { locality: 'Adyar', city: 'Chennai', principalSubdivision: 'Tamil Nadu', countryName: 'India' } } })
    const mod = await import('../reverse-geocode')
    const result = await mod.getAddressFromGPS(13.0, 80.2)
    expect(result).not.toBeNull()
    expect(result!.locality).toBe('Adyar')
    expect(result!.city).toBe('Chennai')
    expect(result!.state).toBe('Tamil Nadu')
    expect(result!.country).toBe('India')
    expect(result!.displayAddress).toBe('Adyar, Tamil Nadu')
  })

  it('getAddressFromGPS returns null on non-ok response', async function () {
    mockFetch.mockResolvedValueOnce({ ok: false })
    const mod = await import('../reverse-geocode')
    const result = await mod.getAddressFromGPS(13.0, 80.2)
    expect(result).toBeNull()
  })

  it('getAddressFromGPS returns null on fetch error', async function () {
    mockFetch.mockRejectedValueOnce(new Error('network'))
    const mod = await import('../reverse-geocode')
    const result = await mod.getAddressFromGPS(13.0, 80.2)
    expect(result).toBeNull()
  })

  it('getAddressFromGPS handles missing locality gracefully', async function () {
    mockFetch.mockResolvedValueOnce({ ok: true, json: async function () { return { city: 'Chennai', principalSubdivision: 'Tamil Nadu', countryName: 'India' } } })
    const mod = await import('../reverse-geocode')
    const result = await mod.getAddressFromGPS(13.0, 80.2)
    expect(result!.locality).toBe('')
    expect(result!.displayAddress).toBe('Tamil Nadu')
  })

  it('getAddressFromGPS shows Unknown Location when no parts', async function () {
    mockFetch.mockResolvedValueOnce({ ok: true, json: async function () { return { countryName: 'India' } } })
    const mod = await import('../reverse-geocode')
    const result = await mod.getAddressFromGPS(13.0, 80.2)
    expect(result!.displayAddress).toBe('Unknown Location')
  })
})
