// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

jest.mock('@/lib/supabase-auth', function() {
  return { getSupabaseBrowserClient: jest.fn(function() { return null }) }
})
jest.mock('@/lib/use-hydrated', function() {
  return { useHydrated: function() { return true } }
})
jest.mock('@/lib/auth/roles', function() {
  return {
    isPublicRoute: function() { return false },
    canAccessRoute: function() { return true },
    getPermissionsForRole: function() { return [] },
  }
})

import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import React from 'react'
import { AuthGuard } from '../auth/AuthGuard'
import { useAppStore } from '@/lib/store'

var pushMock = jest.fn()
jest.mock('next/navigation', function() {
  return { useRouter: function() { return { push: pushMock, replace: pushMock } }, usePathname: function() { return '/assistant' }, useSearchParams: function() { return new URLSearchParams() } }
})

describe('AuthGuard', function() {
  beforeEach(function() {
    pushMock.mockClear()
    useAppStore.setState({
      isAuthenticated: false,
      profileHydrated: true,
      operatorName: '',
      authRole: 'citizen',
      authToken: null,
    })
    Object.defineProperty(process.env, 'NODE_ENV', { value: 'test', configurable: true })
    if (typeof window !== 'undefined') {
      window.localStorage.removeItem('__E2E_SKIP_AUTH__')
    }
  })

  it('renders children when E2E skip-auth flag is set', function() {
    window.localStorage.setItem('__E2E_SKIP_AUTH__', 'true')
    render(React.createElement(AuthGuard, null, React.createElement('div', { 'data-testid': 'child' }, 'Hello')))
    expect(screen.getByTestId('child')).toBeTruthy()
  })

  it('shows loading spinner while checking session', function() {
    render(React.createElement(AuthGuard, null, React.createElement('div', null, 'Hello')))
    expect(screen.getByText(/Verifying session/)).toBeTruthy()
  })

  it('renders children when authenticated', function() {
    useAppStore.setState({ isAuthenticated: true, operatorName: 'TestOp', authRole: 'officer' })
    render(React.createElement(AuthGuard, null, React.createElement('div', { 'data-testid': 'child' }, 'Hello')))
    expect(screen.getByTestId('child')).toBeTruthy()
  })

  it('restores session from supabase when not authenticated', async function() {
    var supabase = require('@/lib/supabase-auth')
    supabase.getSupabaseBrowserClient.mockReturnValueOnce({
      auth: {
        getSession: jest.fn(function() { return Promise.resolve({ data: { session: { user: { user_metadata: { name: 'SessionUser', role: 'officer' }, email: 'op@test.com' }, access_token: 'tok-123' } }, error: null }) }),
      },
    })
    useAppStore.setState({ isAuthenticated: false, profileHydrated: true })
    render(React.createElement(AuthGuard, null, React.createElement('div', { 'data-testid': 'child' }, 'Hello')))
    await waitFor(function() { expect(screen.getByTestId('child')).toBeInTheDocument() })
  })

  it('redirects to landing when no session and not authenticated', async function() {
    render(React.createElement(AuthGuard, null, React.createElement('div', null, 'Hello')))
    await waitFor(function() { expect(pushMock).toHaveBeenCalledWith('/landing') })
  })

  it('shows Access Denied when route not accessible', async function() {
    var roles = require('@/lib/auth/roles')
    roles.canAccessRoute = jest.fn(function() { return false })
    useAppStore.setState({ isAuthenticated: true, operatorName: 'TestOp', authRole: 'citizen' })
    render(React.createElement(AuthGuard, null, React.createElement('div', null, 'Hello')))
    expect(screen.getByText('Access Denied')).toBeInTheDocument()
    fireEvent.click(screen.getByText('Go to Dashboard'))
    expect(pushMock).toHaveBeenCalledWith('/')
  })
})
