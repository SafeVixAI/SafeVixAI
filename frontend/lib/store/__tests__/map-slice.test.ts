// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

import { create } from 'zustand'
import { createMapSlice } from '../map-slice'
import type { MapSlice } from '../map-slice'

describe('MapSlice', function() {
  function createTestStore() {
    return create<MapSlice>()(function(set, get, api) {
      return createMapSlice(set, get, api)
    })
  }

  it('has default values', function() {
    const store = createTestStore()
    const state = store.getState()
    expect(state.showHazardHeatmap).toBe(true)
    expect(state.showSatellite).toBe(false)
    expect(state.showTraffic).toBe(false)
    expect(state.showSafeSpaces).toBe(false)
    expect(state.showEmergencyServices).toBe(true)
    expect(state.mapStatus).toBe('loading')
    expect(state.mapProvider).toBeNull()
    expect(state.mapError).toBeNull()
    expect(state.mapSearchTarget).toBeNull()
  })

  it('toggles hazard heatmap', function() {
    const store = createTestStore()
    store.getState().setShowHazardHeatmap(false)
    expect(store.getState().showHazardHeatmap).toBe(false)
    store.getState().setShowHazardHeatmap(true)
    expect(store.getState().showHazardHeatmap).toBe(true)
  })

  it('toggles satellite view', function() {
    const store = createTestStore()
    store.getState().setShowSatellite(true)
    expect(store.getState().showSatellite).toBe(true)
  })

  it('toggles traffic layer', function() {
    const store = createTestStore()
    store.getState().setShowTraffic(true)
    expect(store.getState().showTraffic).toBe(true)
  })

  it('toggles safe spaces', function() {
    const store = createTestStore()
    store.getState().setShowSafeSpaces(true)
    expect(store.getState().showSafeSpaces).toBe(true)
  })

  it('toggles emergency services', function() {
    const store = createTestStore()
    store.getState().setShowEmergencyServices(false)
    expect(store.getState().showEmergencyServices).toBe(false)
  })

  it('setMapState batch-updates map state', function() {
    const store = createTestStore()
    store.getState().setMapState({ mapStatus: 'ready', mapProvider: 'maptiler-vector', mapError: null })
    const state = store.getState()
    expect(state.mapStatus).toBe('ready')
    expect(state.mapProvider).toBe('maptiler-vector')
    expect(state.mapError).toBeNull()
  })

  it('setMapState handles error state', function() {
    const store = createTestStore()
    store.getState().setMapState({ mapStatus: 'error', mapError: 'Failed to load tiles' })
    expect(store.getState().mapStatus).toBe('error')
    expect(store.getState().mapError).toBe('Failed to load tiles')
  })

  it('setMapSearchTarget sets search target', function() {
    const store = createTestStore()
    const target = { lat: 13.08, lon: 80.27, label: 'Chennai' }
    store.getState().setMapSearchTarget(target)
    expect(store.getState().mapSearchTarget).toEqual(target)
  })

  it('setMapSearchTarget clears search target with null', function() {
    const store = createTestStore()
    store.getState().setMapSearchTarget({ lat: 13.08, lon: 80.27, label: 'Chennai' })
    store.getState().setMapSearchTarget(null)
    expect(store.getState().mapSearchTarget).toBeNull()
  })
})
