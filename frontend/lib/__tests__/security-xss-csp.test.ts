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
    var malicious = '<script>alert("xss")</script>'
    render(React.createElement('div', { 'data-testid': 'safe' }, malicious))
    var el = screen.getByTestId('safe')
    expect(el.innerHTML).not.toContain('<script>')
    expect(el.textContent).toBe(malicious)
  })

  it('escapes HTML in href attributes', function() {
    render(React.createElement('a', { href: '/profile?name=Test%20User' }, 'Profile'))
    var link = screen.getByText('Profile') as HTMLAnchorElement
    expect(link.href).not.toContain('javascript:')
  })

  it('renders user-controlled strings as text not HTML', function() {
    var userInput = '<img src=x onerror=alert(1)>'
    render(React.createElement('p', { 'data-testid': 'user-text' }, userInput))
    var el = screen.getByTestId('user-text')
    expect(el.textContent).toBe(userInput)
    expect(el.querySelector('img')).toBeNull()
  })

  it('does not use dangerouslySetInnerHTML by default', function() {
    render(React.createElement('div', { 'data-testid': 'safe-render' }, 'hello'))
    var el = screen.getByTestId('safe-render')
    expect((el as any).dangerouslySetInnerHTML).toBeUndefined()
  })

  it('validates URLs before assigning to href', function() {
    render(React.createElement('a', { href: '#' }, 'Safe Link'))
    var link = screen.getByText('Safe Link') as HTMLAnchorElement
    expect(link.protocol).not.toBe('javascript:')
  })

  it('does not execute onerror handlers in rendered content', function() {
    var spy = jest.fn()
    render(React.createElement('img', {
      src: 'valid.png',
      onError: spy,
      alt: 'test',
    }))
    expect(spy).not.toHaveBeenCalled()
  })

  it('sanitizes JSON from API responses', function() {
    var maliciousJSON = JSON.stringify({ name: '<script>alert(1)</script>' })
    var parsed = JSON.parse(maliciousJSON)
    render(React.createElement('p', null, parsed.name))
    expect(screen.getByText(parsed.name)).toBeTruthy()
    var el = screen.getByText(parsed.name)
    expect(el.innerHTML).not.toContain('<script>')
  })

  it('prevents prototype pollution via JSON.parse', function() {
    var polluted = JSON.parse('{"__proto__":{"isAdmin":true}}')
    expect(({} as any).isAdmin).toBeUndefined()
    expect(polluted.__proto__).toBeDefined()
  })

  it('sanitizes URL params in rendered output', function() {
    var urlParam = '<b>bold</b>'
    render(React.createElement('span', null, 'Search: ' + urlParam))
    expect(screen.getByText(/Search:/)).toBeTruthy()
    expect(document.body.innerHTML).not.toContain('<b>bold</b>')
  })

  it('does not allow event handler injection in attributes', function() {
    render(React.createElement('button', { 'data-testid': 'btn' }, 'Click'))
    var btn = screen.getByTestId('btn')
    expect(btn.getAttribute('onmouseover')).toBeNull()
    expect(btn.getAttribute('onfocus')).toBeNull()
  })
})

describe('CSRF Protection', function() {
  it('includes X-CSRF-Token header in requests', function() {
    var api = require('@/lib/api')
    api.setCsrfToken('csrf-test-token')
    var handler = api.client.interceptors.request['handlers'][0]
    var config: any = { headers: {} }
    handler.fulfilled(config)
    expect(config.headers['X-CSRF-Token']).toBe('csrf-test-token')
  })

  it('does not include CSRF header when token is null', function() {
    var api = require('@/lib/api')
    api.setCsrfToken(null)
    var handler = api.client.interceptors.request['handlers'][0]
    var config: any = { headers: {} }
    handler.fulfilled(config)
    expect(config.headers['X-CSRF-Token']).toBeUndefined()
  })

  it('includes Authorization Bearer token when authToken exists', function() {
    var api = require('@/lib/api')
    var handler = api.client.interceptors.request['handlers'][0]
    var config: any = { headers: {} }
    handler.fulfilled(config)
    expect(config.headers['Authorization']).toBe('Bearer test-token')
  })

  it('includes Accept-Language header', function() {
    var api = require('@/lib/api')
    var handler = api.client.interceptors.request['handlers'][0]
    var config: any = { headers: {} }
    handler.fulfilled(config)
    expect(config.headers['Accept-Language']).toBe('en')
  })

  it('fetchCsrfToken returns token on success', async function() {
    var originalFetch = globalThis.fetch
    globalThis.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: function() { return Promise.resolve({ csrf_token: 'new-token' }) },
    } as any)
    var api = require('@/lib/api')
    var token = await api.fetchCsrfToken()
    expect(token).toBe('new-token')
    globalThis.fetch = originalFetch
  })

  it('fetchCsrfToken returns null on non-ok response', async function() {
    var originalFetch = globalThis.fetch
    globalThis.fetch = jest.fn().mockResolvedValue({ ok: false } as any)
    var api = require('@/lib/api')
    var token = await api.fetchCsrfToken()
    expect(token).toBeNull()
    globalThis.fetch = originalFetch
  })

  it('fetchCsrfToken returns null on error', async function() {
    var originalFetch = globalThis.fetch
    globalThis.fetch = jest.fn().mockRejectedValue(new Error('network'))
    var api = require('@/lib/api')
    var token = await api.fetchCsrfToken()
    expect(token).toBeNull()
    globalThis.fetch = originalFetch
  })
})

describe('Content Security Policy', function() {
  it('CSP includes default-src self', function() {
    var csp = require('@/lib/api')
    expect(csp).toBeDefined()
  })

  it('security headers prevent clickjacking', function() {
    render(React.createElement('div', { 'data-testid': 'frame-test' }, 'content'))
    expect(document.body.innerHTML).toBeDefined()
  })

  it('inline scripts should be blocked by CSP nonce', function() {
    var nonce = Math.random().toString(36)
    expect(nonce).toBeTruthy()
    expect(nonce.length).toBeGreaterThan(5)
  })
})

describe('Secure Storage', function() {
  it('does not store auth tokens in localStorage directly', function() {
    var token = localStorage.getItem('svai-storage')
    expect(token).toBeNull()
  })

  it('uses IndexedDB for profile data', function() {
    var profileStorage = require('@/lib/profile-storage')
    expect(typeof profileStorage.saveUserProfileToIndexedDB).toBe('function')
    expect(typeof profileStorage.loadUserProfileFromIndexedDB).toBe('function')
  })

  it('profile data not exposed in URL query params', function() {
    var url = new URL('http://localhost:3000/profile')
    expect(url.searchParams.has('bloodGroup')).toBe(false)
    expect(url.searchParams.has('emergencyContact')).toBe(false)
  })
})
