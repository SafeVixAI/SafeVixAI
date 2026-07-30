// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

import { create } from 'zustand'
import { createUISlice } from '../ui-slice'
import type { UISlice } from '../ui-slice'

describe('UISlice', function() {
  function createTestStore() {
    return create<UISlice>()(function(set, get, api) {
      return createUISlice(set, get, api)
    })
  }

  it('has default values', function() {
    const store = createTestStore()
    const state = store.getState()
    expect(state.isSystemSidebarOpen).toBe(false)
    expect(state.isDesktopSidebarCollapsed).toBe(false)
    expect(state.isThinSidebarEnabled).toBe(true)
  })

  it('toggles system sidebar', function() {
    const store = createTestStore()
    store.getState().setSystemSidebarOpen(true)
    expect(store.getState().isSystemSidebarOpen).toBe(true)
    store.getState().setSystemSidebarOpen(false)
    expect(store.getState().isSystemSidebarOpen).toBe(false)
  })

  it('toggles desktop sidebar collapse', function() {
    const store = createTestStore()
    store.getState().setDesktopSidebarCollapsed(true)
    expect(store.getState().isDesktopSidebarCollapsed).toBe(true)
    store.getState().setDesktopSidebarCollapsed(false)
    expect(store.getState().isDesktopSidebarCollapsed).toBe(false)
  })

  it('toggles thin sidebar', function() {
    const store = createTestStore()
    store.getState().setThinSidebarEnabled(false)
    expect(store.getState().isThinSidebarEnabled).toBe(false)
    store.getState().setThinSidebarEnabled(true)
    expect(store.getState().isThinSidebarEnabled).toBe(true)
  })

  it('all sidebar state is independent', function() {
    const store = createTestStore()
    store.getState().setSystemSidebarOpen(true)
    store.getState().setDesktopSidebarCollapsed(true)
    store.getState().setThinSidebarEnabled(false)
    const s = store.getState()
    expect(s.isSystemSidebarOpen).toBe(true)
    expect(s.isDesktopSidebarCollapsed).toBe(true)
    expect(s.isThinSidebarEnabled).toBe(false)
  })
})
