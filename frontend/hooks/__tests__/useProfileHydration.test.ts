jest.mock('@/lib/profile-storage', function() {
  return {
    loadUserProfileFromIndexedDB: jest.fn().mockResolvedValue(null),
    migrateUserProfileFromLocalStorage: jest.fn().mockResolvedValue(undefined),
  }
}, { virtual: false })

jest.mock('@/lib/store', function() {
  var mState = { setUserProfile: jest.fn(), setProfileHydrated: jest.fn() }
  return {
    useAppStore: { getState: jest.fn(function() { return mState }) },
  }
}, { virtual: false })

import { render, waitFor } from '@testing-library/react'
import React from 'react'

var profileStorageMod: any
var storeMod: any

beforeEach(function() {
  jest.clearAllMocks()
  profileStorageMod = require('@/lib/profile-storage')
  storeMod = require('@/lib/store')
})

function TestCase() {
  require('../useProfileHydration').useProfileHydration()
  return React.createElement('div')
}

describe('useProfileHydration', function() {
  it('migrates profile from localStorage on mount', async function() {
    render(React.createElement(TestCase))
    await waitFor(function() { expect(profileStorageMod.migrateUserProfileFromLocalStorage).toHaveBeenCalled() })
  })

  it('loads profile from IndexedDB on mount', async function() {
    render(React.createElement(TestCase))
    await waitFor(function() { expect(profileStorageMod.loadUserProfileFromIndexedDB).toHaveBeenCalled() })
  })

  it('sets profile when IndexedDB has data', async function() {
    var mockProfile = { name: 'Test User', bloodGroup: 'O+' }
    profileStorageMod.loadUserProfileFromIndexedDB.mockResolvedValue(mockProfile)
    render(React.createElement(TestCase))
    await waitFor(function() {
      expect(storeMod.useAppStore.getState().setUserProfile).toHaveBeenCalledWith(mockProfile)
    })
  })

  it('does not set profile when IndexedDB returns null', async function() {
    profileStorageMod.loadUserProfileFromIndexedDB.mockResolvedValue(null)
    render(React.createElement(TestCase))
    await waitFor(function() {
      expect(storeMod.useAppStore.getState().setUserProfile).not.toHaveBeenCalled()
    })
  })

  it('always calls setProfileHydrated', async function() {
    render(React.createElement(TestCase))
    await waitFor(function() {
      expect(storeMod.useAppStore.getState().setProfileHydrated).toHaveBeenCalledWith(true)
    })
  })

  it('cancels profile set on unmount', async function() {
    profileStorageMod.loadUserProfileFromIndexedDB.mockImplementation(function() {
      return new Promise(function(resolve) { setTimeout(function() { resolve({ name: 'Late' } as any) }, 100) })
    })
    var comp = render(React.createElement(TestCase))
    comp.unmount()
    await new Promise(function(r) { return setTimeout(r, 150) })
    expect(storeMod.useAppStore.getState().setUserProfile).not.toHaveBeenCalled()
  })
})
