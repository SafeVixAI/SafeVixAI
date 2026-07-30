// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
describe('map-defaults', function () {
  beforeEach(function () {
    delete process.env.NEXT_PUBLIC_MAP_FALLBACK_LAT
    delete process.env.NEXT_PUBLIC_MAP_FALLBACK_LON
    delete process.env.NEXT_PUBLIC_MAP_FALLBACK_ZOOM
    delete process.env.NEXT_PUBLIC_MAP_DEFAULT_ZOOM
    jest.resetModules()
  })

  it('exports FALLBACK_MAP_CENTER as [lat, lon]', async function () {
    const mod = await import('../map-defaults')
    expect(Array.isArray(mod.FALLBACK_MAP_CENTER)).toBe(true)
    expect(mod.FALLBACK_MAP_CENTER).toHaveLength(2)
    expect(typeof mod.FALLBACK_MAP_CENTER[0]).toBe('number')
    expect(typeof mod.FALLBACK_MAP_CENTER[1]).toBe('number')
  })

  it('exports FALLBACK_MAP_ZOOM and LIVE_MAP_ZOOM as numbers', async function () {
    const mod = await import('../map-defaults')
    expect(typeof mod.FALLBACK_MAP_ZOOM).toBe('number')
    expect(typeof mod.LIVE_MAP_ZOOM).toBe('number')
  })

  it('uses env vars when set', async function () {
    process.env.NEXT_PUBLIC_MAP_FALLBACK_LAT = '12.9716'
    process.env.NEXT_PUBLIC_MAP_FALLBACK_LON = '77.5946'
    process.env.NEXT_PUBLIC_MAP_FALLBACK_ZOOM = '10'
    process.env.NEXT_PUBLIC_MAP_DEFAULT_ZOOM = '15'
    jest.resetModules()
    const mod = await import('../map-defaults')
    expect(mod.FALLBACK_MAP_CENTER[0]).toBe(12.9716)
    expect(mod.FALLBACK_MAP_CENTER[1]).toBe(77.5946)
    expect(mod.FALLBACK_MAP_ZOOM).toBe(10)
    expect(mod.LIVE_MAP_ZOOM).toBe(15)
  })

  it('uses default fallback center when env vars are missing', async function () {
    const mod = await import('../map-defaults')
    expect(mod.FALLBACK_MAP_CENTER[0]).toBe(20.5937)
    expect(mod.FALLBACK_MAP_CENTER[1]).toBe(78.9629)
    expect(mod.FALLBACK_MAP_ZOOM).toBe(5)
    expect(mod.LIVE_MAP_ZOOM).toBe(13)
  })
})
