// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
describe('traffic-layer', function () {
  it('addTrafficLayer calls addSource and addLayer', async function () {
    const mockMap = {
      addSource: jest.fn(),
      addLayer: jest.fn(),
    }
    const mod = await import('../traffic-layer')
    mod.addTrafficLayer(mockMap as any)
    expect(mockMap.addSource).toHaveBeenCalledTimes(2)
    expect(mockMap.addSource).toHaveBeenCalledWith('tomtom-traffic-flow', expect.any(Object))
    expect(mockMap.addSource).toHaveBeenCalledWith('tomtom-incidents', expect.any(Object))
    expect(mockMap.addLayer).toHaveBeenCalledTimes(2)
  })

  it('toggleTrafficLayer does nothing if layer missing', async function () {
    const mockMap = {
      getLayer: jest.fn(function () { return false }),
      setLayoutProperty: jest.fn(),
    }
    const mod = await import('../traffic-layer')
    mod.toggleTrafficLayer(mockMap as any, true)
    expect(mockMap.setLayoutProperty).not.toHaveBeenCalled()
  })

  it('toggleTrafficLayer sets visible when show is true', async function () {
    const mockMap = {
      getLayer: jest.fn(function () { return true }),
      setLayoutProperty: jest.fn(),
    }
    const mod = await import('../traffic-layer')
    mod.toggleTrafficLayer(mockMap as any, true)
    expect(mockMap.setLayoutProperty).toHaveBeenCalledWith('traffic-flow', 'visibility', 'visible')
    expect(mockMap.setLayoutProperty).toHaveBeenCalledWith('traffic-incidents', 'visibility', 'visible')
  })

  it('toggleTrafficLayer sets none when show is false', async function () {
    const mockMap = {
      getLayer: jest.fn(function () { return true }),
      setLayoutProperty: jest.fn(),
    }
    const mod = await import('../traffic-layer')
    mod.toggleTrafficLayer(mockMap as any, false)
    expect(mockMap.setLayoutProperty).toHaveBeenCalledWith('traffic-flow', 'visibility', 'none')
    expect(mockMap.setLayoutProperty).toHaveBeenCalledWith('traffic-incidents', 'visibility', 'none')
  })
})
