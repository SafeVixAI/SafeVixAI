// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

import { create } from 'zustand'
import { createAuthSlice } from '../auth-slice'
import type { AuthSlice } from '../auth-slice'

describe('AuthSlice', function() {
  function createTestStore() {
    return create<AuthSlice>()(function(set, get, api) {
      return createAuthSlice(set, get, api)
    })
  }

  it('has default values', function() {
    const store = createTestStore()
    const state = store.getState()
    expect(state.isAuthenticated).toBe(false)
    expect(state.operatorName).toBe('')
    expect(state.authToken).toBeNull()
    expect(state.authRole).toBe('citizen')
  })

  it('setAuth sets all state', function() {
    const store = createTestStore()
    store.getState().setAuth('John Doe', 'token-123', 'admin')
    const state = store.getState()
    expect(state.isAuthenticated).toBe(true)
    expect(state.operatorName).toBe('John Doe')
    expect(state.authToken).toBe('token-123')
    expect(state.authRole).toBe('admin')
  })

  it('setAuth with minimal arguments', function() {
    const store = createTestStore()
    store.getState().setAuth('Jane')
    const state = store.getState()
    expect(state.isAuthenticated).toBe(true)
    expect(state.operatorName).toBe('Jane')
    expect(state.authToken).toBeNull()
    expect(state.authRole).toBe('citizen')
  })

  it('clearAuth resets to defaults', function() {
    const store = createTestStore()
    store.getState().setAuth('John Doe', 'token-123', 'admin')
    store.getState().clearAuth()
    const state = store.getState()
    expect(state.isAuthenticated).toBe(false)
    expect(state.operatorName).toBe('')
    expect(state.authToken).toBeNull()
    expect(state.authRole).toBe('citizen')
  })

  it('setAuthToken updates only token', function() {
    const store = createTestStore()
    store.getState().setAuth('John', 'old-token')
    store.getState().setAuthToken('new-token')
    expect(store.getState().authToken).toBe('new-token')
    expect(store.getState().isAuthenticated).toBe(true)
  })

  it('setAuthRole updates only role', function() {
    const store = createTestStore()
    store.getState().setAuthRole('officer')
    const state = store.getState()
    expect(state.authRole).toBe('officer')
    expect(state.isAuthenticated).toBe(false)
  })
})
