// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

import { create } from 'zustand'
import { createDataSlice } from '../data-slice'
import type { DataSlice } from '../data-slice'

jest.mock('@/lib/profile-storage', function() {
  return { saveUserProfileToIndexedDB: jest.fn().mockResolvedValue(undefined) }
})
jest.mock('@/lib/crash-detection', function() {
  return { requestCrashPermission: jest.fn().mockResolvedValue(true) }
})
var CrashDetectionModule = require('@/lib/crash-detection')

describe('DataSlice', function() {
  function createTestStore() {
    return create<DataSlice>()(function(set, get, api) {
      return createDataSlice(set, get, api)
    })
  }

  it('has default values', function() {
    var store = createTestStore()
    var state = store.getState()
    expect(state.gpsLocation).toBeNull()
    expect(state.gpsError).toBeNull()
    expect(state.nearbyServices).toEqual([])
    expect(state.aiMode).toBe('online')
    expect(state.connectivity).toBe('online')
    expect(state.profileHydrated).toBe(false)
    expect(state.crashDetectionEnabled).toBe(false)
    expect(state.drivingScore).toBeNull()
    expect(state.garageVehicles).toEqual([])
  })

  it('setGpsLocation sets location and clears error', function() {
    var store = createTestStore()
    store.getState().setGpsError('GPS unavailable')
    store.getState().setGpsLocation({ lat: 13.08, lng: 80.27 })
    var state = store.getState()
    expect(state.gpsLocation).toEqual({ lat: 13.08, lng: 80.27 })
    expect(state.gpsError).toBeNull()
  })

  it('setGpsError sets error string', function() {
    var store = createTestStore()
    store.getState().setGpsError('Permission denied')
    expect(store.getState().gpsError).toBe('Permission denied')
  })

  it('setNearbyServices updates services', function() {
    var store = createTestStore()
    var services = [{ id: '1', name: 'Hospital A', category: 'hospital', lat: 13.0, lng: 80.0, distance: 500, phone: '123' }]
    store.getState().setNearbyServices(services)
    expect(store.getState().nearbyServices).toEqual(services)
  })

  it('setServiceRadius changes radius', function() {
    var store = createTestStore()
    store.getState().setServiceRadius(10000)
    expect(store.getState().serviceRadius).toBe(10000)
  })

  it('setAiMode changes AI mode', function() {
    var store = createTestStore()
    store.getState().setAiMode('offline')
    expect(store.getState().aiMode).toBe('offline')
    store.getState().setAiMode('online')
    expect(store.getState().aiMode).toBe('online')
  })

  it('setConnectivity changes connectivity state', function() {
    var store = createTestStore()
    store.getState().setConnectivity('offline')
    expect(store.getState().connectivity).toBe('offline')
  })

  it('setUserProfile merges partial profile', function() {
    var store = createTestStore()
    store.getState().setUserProfile({ name: 'Test User', phone: '+911234567890' })
    var profile = store.getState().userProfile
    expect(profile.name).toBe('Test User')
    expect(profile.phone).toBe('+911234567890')
  })

  it('setUserProfile updates existing fields', function() {
    var store = createTestStore()
    store.getState().setUserProfile({ name: 'First' })
    store.getState().setUserProfile({ bloodGroup: 'O+' })
    var profile = store.getState().userProfile
    expect(profile.name).toBe('First')
    expect(profile.bloodGroup).toBe('O+')
  })

  it('setChallanState updates challan state', function() {
    var store = createTestStore()
    store.getState().setChallanState({ violation: '185', vehicle: '4w', jurisdiction: 'Delhi (DL)', isRepeat: true })
    var cs = store.getState().challanState
    expect(cs.violation).toBe('185')
    expect(cs.jurisdiction).toBe('Delhi (DL)')
    expect(cs.isRepeat).toBe(true)
  })

  it('setDrivingScore updates score', function() {
    var store = createTestStore()
    store.getState().setDrivingScore(85)
    expect(store.getState().drivingScore).toBe(85)
    store.getState().setDrivingScore(null)
    expect(store.getState().drivingScore).toBeNull()
  })

  it('setCrashDetectionEnabled sets flag', async function() {
    var store = createTestStore()
    await store.getState().setCrashDetectionEnabled(true)
    expect(store.getState().crashDetectionEnabled).toBe(true)
  })

  it('setModelLoadProgress updates progress', function() {
    var store = createTestStore()
    store.getState().setModelLoadProgress(50)
    expect(store.getState().modelLoadProgress).toBe(50)
  })

  it('setServerWarming toggles flag', function() {
    var store = createTestStore()
    store.getState().setServerWarming(true)
    expect(store.getState().serverWarming).toBe(true)
  })

  it('setGarageVehicles sets vehicles', function() {
    var store = createTestStore()
    var vehicles = [{ id: 'v1', plate: 'TN01AB1234' }]
    store.getState().setGarageVehicles(vehicles)
    expect(store.getState().garageVehicles).toEqual(vehicles)
  })

  it('setProfileHydrated toggles flag', function() {
    var store = createTestStore()
    store.getState().setProfileHydrated(true)
    expect(store.getState().profileHydrated).toBe(true)
  })

  it('setServiceCategory sets category', function() {
    var store = createTestStore()
    store.getState().setServiceCategory('hospital')
    expect(store.getState().serviceCategory).toBe('hospital')
  })

  it('setNearbyRoadIssues updates road issues', function() {
    var store = createTestStore()
    var issues = [{ id: 'r1', type: 'pothole', lat: 13.0, lng: 80.0, description: 'Big pothole' }]
    store.getState().setNearbyRoadIssues(issues)
    expect(store.getState().nearbyRoadIssues).toEqual(issues)
  })

  it('setRiskAnalysis updates risk data', function() {
    var store = createTestStore()
    store.getState().setRiskAnalysis({ riskScore: 75, riskLevel: 'medium', estimatedLiability: 5000, predictedViolationsCount: 2, recommendations: ['Drive carefully'] })
    var ra = store.getState().riskAnalysis
    expect(ra.riskScore).toBe(75)
    expect(ra.riskLevel).toBe('medium')
    expect(ra.recommendations).toEqual(['Drive carefully'])
  })

  it('setCrashDetectionEnabled permission denied shows toast', async function() {
    CrashDetectionModule.requestCrashPermission.mockResolvedValueOnce(false)
    var store = createTestStore()
    await store.getState().setCrashDetectionEnabled(true)
    expect(store.getState().crashDetectionEnabled).toBe(false)
  })

  it('setCrashDetectionEnabled handles error', async function() {
    CrashDetectionModule.requestCrashPermission.mockRejectedValueOnce(new Error('permission error'))
    var store = createTestStore()
    var consoleSpy = jest.spyOn(console, 'error').mockImplementation(function() {})
    await store.getState().setCrashDetectionEnabled(true)
    expect(store.getState().crashDetectionEnabled).toBe(false)
    consoleSpy.mockRestore()
  })

  it('setCrashDetectionEnabled false skips permission check', async function() {
    var store = createTestStore()
    await store.getState().setCrashDetectionEnabled(true)
    expect(store.getState().crashDetectionEnabled).toBe(true)
    await store.getState().setCrashDetectionEnabled(false)
    expect(store.getState().crashDetectionEnabled).toBe(false)
  })

  it('setLastSyncedGarage updates timestamp', function() {
    var store = createTestStore()
    store.getState().setLastSyncedGarage(1234567890)
    expect(store.getState().lastSyncedGarage).toBe(1234567890)
    store.getState().setLastSyncedGarage(null)
    expect(store.getState().lastSyncedGarage).toBeNull()
  })
})
