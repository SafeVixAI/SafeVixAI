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
})
