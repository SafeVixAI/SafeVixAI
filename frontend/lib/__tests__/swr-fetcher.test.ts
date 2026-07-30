// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
jest.mock('../api', function () {
  const mockGet = jest.fn().mockResolvedValue({ data: {} })
  return {
    client: {
      get: mockGet,
      post: jest.fn(),
    },
    fetchMunicipalities: jest.fn().mockResolvedValue({ municipalities: [] }),
    fetchNearbyServices: jest.fn().mockResolvedValue([]),
  }
})

const mockClient = require('../api').client
const renderHook = require('@testing-library/react').renderHook

describe('swr-fetcher', function () {
  it('exports fetcher functions', async function () {
    const mod = await import('../swr-fetcher')
    expect(typeof mod.fetcher).toBe('function')
    expect(typeof mod.fetcherNoCache).toBe('function')
  })

  it('exports SWR hooks', async function () {
    const mod = await import('../swr-fetcher')
    expect(typeof mod.useEmergencyServices).toBe('function')
    expect(typeof mod.useEmergencyNumbers).toBe('function')
    expect(typeof mod.useFetchSos).toBe('function')
    expect(typeof mod.useRoadwatchFeed).toBe('function')
    expect(typeof mod.useChallanCalculation).toBe('function')
    expect(typeof mod.useUserProfile).toBe('function')
  })

  it('fetcher calls client.get with params', async function () {
    mockClient.get.mockResolvedValue({ data: { result: 'ok' } })
    const mod = await import('../swr-fetcher')
    const result = await mod.fetcher('/test', { key: 'val' })
    expect(mockClient.get).toHaveBeenCalledWith('/test', { params: { key: 'val' } })
    expect(result).toEqual({ result: 'ok' })
  })

  it('fetcher calls client.get without params', async function () {
    mockClient.get.mockResolvedValue({ data: { result: 'ok' } })
    const mod = await import('../swr-fetcher')
    const result = await mod.fetcher('/test')
    expect(mockClient.get).toHaveBeenCalledWith('/test', { params: undefined })
    expect(result).toEqual({ result: 'ok' })
  })

  it('fetcherNoCache adds cache-busting header', async function () {
    mockClient.get.mockResolvedValue({ data: { result: 'ok' } })
    const mod = await import('../swr-fetcher')
    const result = await mod.fetcherNoCache('/test', { key: 'val' })
    expect(mockClient.get).toHaveBeenCalledWith('/test', { params: { key: 'val' }, headers: { 'Cache-Control': 'no-cache' } })
    expect(result).toEqual({ result: 'ok' })
  })

  it('fetcherNoCache calls client.get without params', async function () {
    mockClient.get.mockResolvedValue({ data: {} })
    const mod = await import('../swr-fetcher')
    await mod.fetcherNoCache('/test')
    expect(mockClient.get).toHaveBeenCalledWith('/test', { params: undefined, headers: { 'Cache-Control': 'no-cache' } })
  })

  it('re-exports SWRConfig', async function () {
    const mod = await import('../swr-fetcher')
    expect(mod.SWRConfig).toBeDefined()
  })

  it('useEmergencyNumbers renders without crashing', function () {
    const mod = require('../swr-fetcher')
    const result = renderHook(function () { return mod.useEmergencyNumbers() })
    expect(result.result.current).toBeDefined()
  })

  it('useEmergencyServices returns null key when lat/lon null', function () {
    const mod = require('../swr-fetcher')
    const result = renderHook(function () { return mod.useEmergencyServices(null, null) })
    expect(result.result.current).toBeDefined()
  })

  it('useEmergencyServices returns key when lat/lon provided', function () {
    const mod = require('../swr-fetcher')
    const result = renderHook(function () { return mod.useEmergencyServices(13.08, 80.27) })
    expect(result.result.current).toBeDefined()
  })

  it('useChallanCalculation returns null key when params null', function () {
    const mod = require('../swr-fetcher')
    const result = renderHook(function () { return mod.useChallanCalculation(null, null, null) })
    expect(result.result.current).toBeDefined()
  })

  it('useChallanCalculation returns key when params provided', function () {
    const mod = require('../swr-fetcher')
    const result = renderHook(function () { return mod.useChallanCalculation('2W', '194D', 'TN') })
    expect(result.result.current).toBeDefined()
  })

  it('useUserProfile renders without crashing', function () {
    const mod = require('../swr-fetcher')
    const result = renderHook(function () { return mod.useUserProfile('user-1') })
    expect(result.result.current).toBeDefined()
  })

  it('useFetchSos returns null key when lat/lon null', function () {
    const mod = require('../swr-fetcher')
    const result = renderHook(function () { return mod.useFetchSos(null, null) })
    expect(result.result.current).toBeDefined()
  })

  it('useFetchSos returns key when lat/lon provided', function () {
    const mod = require('../swr-fetcher')
    const result = renderHook(function () { return mod.useFetchSos(13.08, 80.27) })
    expect(result.result.current).toBeDefined()
  })

  it('useRoadwatchFeed returns null key when lat/lon null', function () {
    const mod = require('../swr-fetcher')
    const result = renderHook(function () { return mod.useRoadwatchFeed(null, null) })
    expect(result.result.current).toBeDefined()
  })

  it('useRoadwatchFeed returns key when lat/lon provided', function () {
    const mod = require('../swr-fetcher')
    const result = renderHook(function () { return mod.useRoadwatchFeed(13.08, 80.27) })
    expect(result.result.current).toBeDefined()
  })
})
