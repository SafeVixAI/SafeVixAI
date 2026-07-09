jest.mock('@/lib/supabase-auth', function() {
  var mGetSession = jest.fn().mockResolvedValue({ data: { session: null } })
  var mUnsub = jest.fn()
  var mOnAuth = jest.fn().mockReturnValue({ data: { subscription: { unsubscribe: mUnsub } } })
  return {
    __mockGetSession: mGetSession,
    __mockUnsub: mUnsub,
    getSupabaseBrowserClient: jest.fn(),
  }
}, { virtual: false })

jest.mock('@/lib/store', function() {
  var mState = { clearAuth: jest.fn(), setAuth: jest.fn(), setUserProfile: jest.fn() }
  return {
    __mockState: mState,
    useAppStore: { getState: jest.fn(function() { return mState }) },
  }
}, { virtual: false })

import { render, waitFor } from '@testing-library/react'
import React from 'react'

var supabaseMod: any
var storeMod: any

beforeEach(function() {
  jest.clearAllMocks()
  supabaseMod = require('@/lib/supabase-auth')
  storeMod = require('@/lib/store')
  supabaseMod.getSupabaseBrowserClient.mockImplementation(function() {
    return { auth: { getSession: supabaseMod.__mockGetSession, onAuthStateChange: jest.fn(function() {
      return { data: { subscription: { unsubscribe: supabaseMod.__mockUnsub } } }
    }) } }
  })
})

function TestCase() {
  require('../useSupabaseSession').useSupabaseSession()
  return React.createElement('div')
}

describe('useSupabaseSession', function() {
  it('does nothing when supabase client is null', function() {
    supabaseMod.getSupabaseBrowserClient.mockReturnValue(null)
    render(React.createElement(TestCase))
    expect(storeMod.__mockState.clearAuth).not.toHaveBeenCalled()
  })

  it('clears auth when session is null', async function() {
    render(React.createElement(TestCase))
    await waitFor(function() { expect(storeMod.__mockState.clearAuth).toHaveBeenCalled() })
  })

  it('sets auth when session exists', async function() {
    supabaseMod.__mockGetSession.mockResolvedValue({
      data: { session: { access_token: 'tok', user: { email: 'test@test.com', user_metadata: {} } } },
    })
    render(React.createElement(TestCase))
    await waitFor(function() { expect(storeMod.__mockState.setAuth).toHaveBeenCalledWith('test@test.com') })
  })

  it('uses display name from user_metadata when available', async function() {
    supabaseMod.__mockGetSession.mockResolvedValue({
      data: { session: { access_token: 'tok', user: { email: 'test@test.com', user_metadata: { name: 'Alice' } } } },
    })
    render(React.createElement(TestCase))
    await waitFor(function() { expect(storeMod.__mockState.setAuth).toHaveBeenCalledWith('Alice') })
  })

  it('unsubscribes on unmount', function() {
    supabaseMod.__mockGetSession.mockResolvedValue({
      data: { session: { access_token: 'tok', user: { email: 'a@b.com', user_metadata: {} } } },
    })
    var comp = render(React.createElement(TestCase))
    comp.unmount()
    expect(supabaseMod.__mockUnsub).toHaveBeenCalled()
  })
})
