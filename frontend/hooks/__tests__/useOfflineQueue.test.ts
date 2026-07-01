// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

var mockEnqueueSOS = jest.fn()
var mockSyncSOS = jest.fn().mockResolvedValue(undefined)
var mockSyncRoad = jest.fn().mockResolvedValue(undefined)

jest.mock('@/lib/offline-sos-queue', () => ({
  enqueueSOS: function() { return mockEnqueueSOS.apply(null, arguments) },
  syncOfflineSOSQueue: function() { return mockSyncSOS() },
  syncOfflineRoadReportQueue: function() { return mockSyncRoad() },
}))

var mockConnectivity = 'offline'
jest.mock('@/lib/store', () => ({
  useAppStore: function(selector) { return selector({ connectivity: mockConnectivity }) },
}))

import { renderHook, act } from '@testing-library/react'

beforeEach(function() {
  mockConnectivity = 'offline'
  mockEnqueueSOS.mockReset().mockResolvedValue(undefined)
  mockSyncSOS.mockReset().mockResolvedValue(undefined)
  mockSyncRoad.mockReset().mockResolvedValue(undefined)
})

describe('useOfflineQueue', function() {
  it('returns isSyncing false initially', function() {
    var { result } = renderHook(() => require('../useOfflineQueue').useOfflineQueue())
    expect(result.current.isSyncing).toBe(false)
  })

  it('enqueueSosItem calls enqueueSOS with data', async function() {
    var { result } = renderHook(() => require('../useOfflineQueue').useOfflineQueue())
    var data = { lat: 13.08, lon: 80.27 }
    await act(async () => { await result.current.enqueueSosItem(data) })
    expect(mockEnqueueSOS).toHaveBeenCalledWith(data)
  })

  it('triggerSync calls both sync functions', async function() {
    var { result } = renderHook(() => require('../useOfflineQueue').useOfflineQueue())
    await act(async () => { await result.current.triggerSync() })
    expect(mockSyncSOS).toHaveBeenCalled()
    expect(mockSyncRoad).toHaveBeenCalled()
  })

  it('sets isSyncing true during sync and false after', async function() {
    var resolveSync
    mockSyncSOS.mockImplementation(() => new Promise(function(r) { resolveSync = r }))
    mockSyncRoad.mockImplementation(() => Promise.resolve())
    var { result } = renderHook(() => require('../useOfflineQueue').useOfflineQueue())
    var syncPromise
    act(function() { syncPromise = result.current.triggerSync() })
    expect(result.current.isSyncing).toBe(true)
    await act(async function() { resolveSync(); await syncPromise })
    expect(result.current.isSyncing).toBe(false)
  })

  it('auto-syncs when connectivity becomes online', function() {
    mockConnectivity = 'online'
    renderHook(() => require('../useOfflineQueue').useOfflineQueue())
    // useOfflineQueue effect fires triggerSync() when connectivity === 'online'
    expect(mockSyncSOS).toHaveBeenCalled()
    expect(mockSyncRoad).toHaveBeenCalled()
  })

  it('does not auto-sync when connectivity stays offline', function() {
    mockConnectivity = 'offline'
    renderHook(() => require('../useOfflineQueue').useOfflineQueue())
    expect(mockSyncSOS).not.toHaveBeenCalled()
  })
})


