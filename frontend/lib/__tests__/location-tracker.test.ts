// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
navigator.geolocation = { watchPosition: jest.fn(), clearWatch: jest.fn() } as any

describe('location-tracker', function () {
  let mockMap: any

  beforeEach(function () {
    mockMap = {
      getSource: jest.fn(),
      addSource: jest.fn(),
      addLayer: jest.fn(),
    }
    ;(navigator.geolocation.watchPosition as jest.Mock).mockReset()
    ;(navigator.geolocation.clearWatch as jest.Mock).mockReset()
  })

  it('starts tracking and returns cleanup', async function () {
    mockMap.getSource.mockReturnValue({ setData: jest.fn() })
    ;(navigator.geolocation.watchPosition as jest.Mock).mockImplementation(function (success: any) { success({ coords: { longitude: 80, latitude: 13, accuracy: 10 } }); return 42 })
    const mod = await import('../location-tracker')
    const cleanup = mod.startLocationTracking(mockMap, {})
    expect(navigator.geolocation.watchPosition).toHaveBeenCalled()
    cleanup()
    expect(navigator.geolocation.clearWatch).toHaveBeenCalledWith(42)
  })

  it('adds source and layers when not present', async function () {
    mockMap.getSource.mockReturnValue(null)
    ;(navigator.geolocation.watchPosition as jest.Mock).mockImplementation(function (_s: any, _e: any) { return 1 })
    const mod = await import('../location-tracker')
    mod.startLocationTracking(mockMap)
    expect(mockMap.addSource).toHaveBeenCalledWith('user-location', expect.any(Object))
    expect(mockMap.addLayer).toHaveBeenCalled()
  })

  it('does not re-add if source exists', async function () {
    mockMap.getSource.mockReturnValue({ setData: jest.fn() })
    ;(navigator.geolocation.watchPosition as jest.Mock).mockImplementation(function (_s: any, _e: any) { return 1 })
    const mod = await import('../location-tracker')
    mod.startLocationTracking(mockMap)
    expect(mockMap.addSource).not.toHaveBeenCalled()
  })

  it('handles geolocation error', async function () {
    const errorFn = jest.fn()
    ;(navigator.geolocation.watchPosition as jest.Mock).mockImplementation(function (_s: any, err: any) { err({ code: 1, message: 'denied' }) })
    const mod = await import('../location-tracker')
    mod.startLocationTracking(mockMap, { onError: errorFn })
  })
})
