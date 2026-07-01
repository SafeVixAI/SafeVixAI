import { create } from 'zustand'
import { createProvidersSlice } from '../providers-slice'
import type { ProvidersSlice } from '../providers-slice'

describe('ProvidersSlice', function() {
  function createTestStore() {
    return create<ProvidersSlice>()(function(set, get, api) {
      return createProvidersSlice(set, get, api)
    })
  }

  it('has default values', function() {
    var store = createTestStore()
    var state = store.getState()
    expect(state.selectedProvider).toBeNull()
  })

  it('sets selectedProvider with full object', function() {
    var store = createTestStore()
    store.getState().setSelectedProvider({ providerName: 'groq', model: 'llama-3.1-8b-instant', displayName: 'Groq' })
    var state = store.getState()
    expect(state.selectedProvider).toEqual({ providerName: 'groq', model: 'llama-3.1-8b-instant', displayName: 'Groq' })
  })

  it('clears selectedProvider to null', function() {
    var store = createTestStore()
    store.getState().setSelectedProvider({ providerName: 'groq', model: 'llama-3.1-8b-instant', displayName: 'Groq' })
    expect(store.getState().selectedProvider).not.toBeNull()
    store.getState().setSelectedProvider(null)
    expect(store.getState().selectedProvider).toBeNull()
  })

  it('sets activeFallbackChain', function() {
    var store = createTestStore()
    store.getState().setActiveFallbackChain(['groq', 'gemini'])
    expect(store.getState().activeFallbackChain).toEqual(['groq', 'gemini'])
  })

  it('sets providerSyncStatus to syncing', function() {
    var store = createTestStore()
    store.getState().setProviderSyncStatus('syncing')
    expect(store.getState().providerSyncStatus).toBe('syncing')
  })

  it('sets providerSyncStatus to error', function() {
    var store = createTestStore()
    store.getState().setProviderSyncStatus('error')
    expect(store.getState().providerSyncStatus).toBe('error')
  })
})
