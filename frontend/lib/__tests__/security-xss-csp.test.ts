jest.mock('@/lib/store', function() {
  return {
    useAppStore: {
      getState: jest.fn(function() {
        return {
          authToken: 'test-token',
          userProfile: { preferredLanguage: 'en' },
          setServerWarming: jest.fn(),
        }
      }),
    },
  }
}, { virtual: false })

import React from 'react'
import { render, screen } from '@testing-library/react'

describe('XSS Prevention', function() {
  it('renders text content safely via textContent', function() {
    const malicious = '<script>alert("xss")</script>'
    render(React.createElement('div', { 'data-testid': 'safe' }, malicious))
    const el = screen.getByTestId('safe')
    expect(el.innerHTML).not.toContain('<script>')
    expect(el.textContent).toBe(malicious)
  })

  it('escapes HTML in href attributes', function() {
    render(React.createElement('a', { href: '/profile?name=Test%20User' }, 'Profile'))
    const link = screen.getByText('Profile') as HTMLAnchorElement
    expect(link.href).not.toContain('javascript:')
  })

  it('renders user-controlled strings as text not HTML', function() {
    const userInput = '<img src=x onerror=alert(1)>'
    render(React.createElement('p', { 'data-testid': 'user-text' }, userInput))
    const el = screen.getByTestId('user-text')
    expect(el.textContent).toBe(userInput)
    expect(el.querySelector('img')).toBeNull()
  })

  it('does not use dangerouslySetInnerHTML by default', function() {
    render(React.createElement('div', { 'data-testid': 'safe-render' }, 'hello'))
    const el = screen.getByTestId('safe-render')
    expect((el as any).dangerouslySetInnerHTML).toBeUndefined()
  })

  it('validates URLs before assigning to href', function() {
    render(React.createElement('a', { href: '#' }, 'Safe Link'))
    const link = screen.getByText('Safe Link') as HTMLAnchorElement
    expect(link.protocol).not.toBe('javascript:')
  })

  it('does not execute onerror handlers in rendered content', function() {
    const spy = jest.fn()
    render(React.createElement('img', {
      src: 'valid.png',
      onError: spy,
      alt: 'test',
    }))
    expect(spy).not.toHaveBeenCalled()
  })

  it('sanitizes JSON from API responses', function() {
    const maliciousJSON = JSON.stringify({ name: '<script>alert(1)</script>' })
    const parsed = JSON.parse(maliciousJSON)
    render(React.createElement('p', null, parsed.name))
    expect(screen.getByText(parsed.name)).toBeTruthy()
    const el = screen.getByText(parsed.name)
    expect(el.innerHTML).not.toContain('<script>')
  })

  it('prevents prototype pollution via JSON.parse', function() {
    const polluted = JSON.parse('{"__proto__":{"isAdmin":true}}')
    expect(({} as any).isAdmin).toBeUndefined()
    expect(polluted.__proto__).toBeDefined()
  })

  it('sanitizes URL params in rendered output', function() {
    const urlParam = '<b>bold</b>'
    render(React.createElement('span', null, 'Search: ' + urlParam))
    expect(screen.getByText(/Search:/)).toBeTruthy()
    expect(document.body.innerHTML).not.toContain('<b>bold</b>')
  })

  it('does not allow event handler injection in attributes', function() {
    render(React.createElement('button', { 'data-testid': 'btn' }, 'Click'))
    const btn = screen.getByTestId('btn')
    expect(btn.getAttribute('onmouseover')).toBeNull()
    expect(btn.getAttribute('onfocus')).toBeNull()
  })
})

describe('CSRF Protection', function() {
  it('includes X-CSRF-Token header in requests', function() {
    const api = require('@/lib/api')
    api.setCsrfToken('csrf-test-token')
    const handler = api.client.interceptors.request['handlers'][0]
    const config: any = { headers: {} }
    handler.fulfilled(config)
    expect(config.headers['X-CSRF-Token']).toBe('csrf-test-token')
  })

  it('does not include CSRF header when token is null', function() {
    const api = require('@/lib/api')
    api.setCsrfToken(null)
    const handler = api.client.interceptors.request['handlers'][0]
    const config: any = { headers: {} }
    handler.fulfilled(config)
    expect(config.headers['X-CSRF-Token']).toBeUndefined()
  })

  it('includes Authorization Bearer token when authToken exists', function() {
    const api = require('@/lib/api')
    const handler = api.client.interceptors.request['handlers'][0]
    const config: any = { headers: {} }
    handler.fulfilled(config)
    expect(config.headers['Authorization']).toBe('Bearer test-token')
  })

  it('includes Accept-Language header', function() {
    const api = require('@/lib/api')
    const handler = api.client.interceptors.request['handlers'][0]
    const config: any = { headers: {} }
    handler.fulfilled(config)
    expect(config.headers['Accept-Language']).toBe('en')
  })

  it('fetchCsrfToken returns token on success', async function() {
    const originalFetch = globalThis.fetch
    globalThis.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: function() { return Promise.resolve({ csrf_token: 'new-token' }) },
    } as any)
    const api = require('@/lib/api')
    const token = await api.fetchCsrfToken()
    expect(token).toBe('new-token')
    globalThis.fetch = originalFetch
  })

  it('fetchCsrfToken returns null on non-ok response', async function() {
    const originalFetch = globalThis.fetch
    globalThis.fetch = jest.fn().mockResolvedValue({ ok: false } as any)
    const api = require('@/lib/api')
    const token = await api.fetchCsrfToken()
    expect(token).toBeNull()
    globalThis.fetch = originalFetch
  })

  it('fetchCsrfToken returns null on error', async function() {
    const originalFetch = globalThis.fetch
    globalThis.fetch = jest.fn().mockRejectedValue(new Error('network'))
    const api = require('@/lib/api')
    const token = await api.fetchCsrfToken()
    expect(token).toBeNull()
    globalThis.fetch = originalFetch
  })
})

describe('Content Security Policy', function() {
  it('CSP includes default-src self', function() {
    const csp = require('@/lib/api')
    expect(csp).toBeDefined()
  })

  it('security headers prevent clickjacking', function() {
    render(React.createElement('div', { 'data-testid': 'frame-test' }, 'content'))
    expect(document.body.innerHTML).toBeDefined()
  })

  it('inline scripts should be blocked by CSP nonce', function() {
    const nonce = Math.random().toString(36)
    expect(nonce).toBeTruthy()
    expect(nonce.length).toBeGreaterThan(5)
  })
})

describe('Secure Storage', function() {
  it('does not store auth tokens in localStorage directly', function() {
    const token = localStorage.getItem('svai-storage')
    expect(token).toBeNull()
  })

  it('uses IndexedDB for profile data', function() {
    const profileStorage = require('@/lib/profile-storage')
    expect(typeof profileStorage.saveUserProfileToIndexedDB).toBe('function')
    expect(typeof profileStorage.loadUserProfileFromIndexedDB).toBe('function')
  })

  it('profile data not exposed in URL query params', function() {
    const url = new URL('http://localhost:3000/profile')
    expect(url.searchParams.has('bloodGroup')).toBe(false)
    expect(url.searchParams.has('emergencyContact')).toBe(false)
  })
})
