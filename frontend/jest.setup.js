// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

import '@testing-library/jest-dom'

// ── Polyfills ────────────────────────────────────────────────
if (!Element.prototype.scrollTo) {
  Element.prototype.scrollTo = function() {}
}
if (!globalThis.fetch) {
  globalThis.fetch = jest.fn().mockResolvedValue({ json: jest.fn() })
}

Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation(function(query) {
    return {
      matches: false,
      media: query,
      onchange: null,
      addListener: jest.fn(),
      removeListener: jest.fn(),
      addEventListener: jest.fn(),
      removeEventListener: jest.fn(),
      dispatchEvent: jest.fn(),
    }
  }),
})

// ── Mock heavy WebGL / WASM / ML dependencies ──────────────────────

jest.mock('maplibre-gl', () => ({
  Map: jest.fn(() => ({
    on: jest.fn(),
    remove: jest.fn(),
    resize: jest.fn(),
    getCenter: jest.fn(() => ({ lat: 0, lng: 0 })),
    getZoom: jest.fn(() => 5),
    setCenter: jest.fn(),
    setZoom: jest.fn(),
    flyTo: jest.fn(),
    addSource: jest.fn(),
    addLayer: jest.fn(),
    removeLayer: jest.fn(),
    removeSource: jest.fn(),
    getSource: jest.fn(),
    getLayer: jest.fn(),
    project: jest.fn(() => ({ x: 0, y: 0 })),
    unproject: jest.fn(() => ({ lat: 0, lng: 0 })),
    getBounds: jest.fn(() => ({ getNorth: () => 1, getSouth: () => -1, getEast: () => 1, getWest: () => -1 })),
    fitBounds: jest.fn(),
    once: jest.fn(),
    off: jest.fn(),
    getCanvas: jest.fn(() => ({ style: {} })),
    loaded: jest.fn(() => true),
  })),
  Popup: jest.fn(() => ({
    setLngLat: jest.fn().mockReturnThis(),
    setHTML: jest.fn().mockReturnThis(),
    addTo: jest.fn().mockReturnThis(),
    remove: jest.fn(),
    setDOMContent: jest.fn().mockReturnThis(),
  })),
  Marker: jest.fn(() => ({
    setLngLat: jest.fn().mockReturnThis(),
    addTo: jest.fn().mockReturnThis(),
    remove: jest.fn(),
    setPopup: jest.fn().mockReturnThis(),
    getElement: jest.fn(() => document.createElement('div')),
  })),
  NavigationControl: jest.fn(),
  GeolocateControl: jest.fn(),
  AttributionControl: jest.fn(),
  ScaleControl: jest.fn(),
}))

jest.mock('@mlc-ai/web-llm', () => ({
  CreateMLCEngine: jest.fn().mockResolvedValue({
    chat: { completions: { create: jest.fn().mockResolvedValue({ choices: [{ message: { content: 'mock' } }] }) } },
    interruptGenerate: jest.fn(),
    unload: jest.fn(),
  }),
  MLCEngine: jest.fn(),
}), { virtual: true })

jest.mock('@duckdb/duckdb-wasm', () => ({
  createDuckDB: jest.fn().mockResolvedValue({
    connect: jest.fn().mockResolvedValue({ query: jest.fn(), close: jest.fn() }),
    registerFile: jest.fn(),
    close: jest.fn(),
  }),
  createConnection: jest.fn(),
  createDuckDBProvider: jest.fn(),
}))

jest.mock('@huggingface/transformers', () => ({
  pipeline: jest.fn().mockResolvedValue(jest.fn()),
  env: { useBrowserCache: false, backends: { onnx: { wasm: {} } } },
}))

jest.mock('idb', () => {
  var mockDB = {
    createObjectStore: jest.fn(),
    put: jest.fn().mockResolvedValue(undefined),
    get: jest.fn().mockResolvedValue(undefined),
    getAll: jest.fn().mockResolvedValue([]),
    delete: jest.fn().mockResolvedValue(undefined),
    clear: jest.fn().mockResolvedValue(undefined),
    transaction: jest.fn().mockReturnValue({ objectStore: jest.fn(), done: Promise.resolve() }),
  }
  return {
    openDB: jest.fn().mockResolvedValue(mockDB),
    deleteDB: jest.fn(),
  }
})

jest.mock('gsap/ScrollTrigger', () => ({ ScrollTrigger: { refresh: jest.fn() } }))
jest.mock('gsap/CustomEase', () => ({ CustomEase: { create: jest.fn() } }))

jest.mock('gsap', () => {
  var gsapObj = {
    to: jest.fn().mockReturnThis(),
    from: jest.fn().mockReturnThis(),
    fromTo: jest.fn().mockReturnThis(),
    set: jest.fn().mockReturnThis(),
    timeline: jest.fn(function() {
      return {
        to: jest.fn().mockReturnThis(),
        from: jest.fn().mockReturnThis(),
        fromTo: jest.fn().mockReturnThis(),
        set: jest.fn().mockReturnThis(),
        play: jest.fn().mockReturnThis(),
        pause: jest.fn().mockReturnThis(),
        reverse: jest.fn().mockReturnThis(),
        kill: jest.fn(),
        clear: jest.fn(),
        progress: jest.fn(),
        totalProgress: jest.fn(),
        seek: jest.fn(),
        add: jest.fn().mockReturnThis(),
        eventCallback: jest.fn().mockReturnThis(),
        addLabel: jest.fn(),
      }
    }),
    registerPlugin: jest.fn(),
    matchMedia: jest.fn(function() { return { add: jest.fn(), remove: jest.fn() } }),
    kill: jest.fn(),
    getById: jest.fn(),
    context: jest.fn(function() { return { add: jest.fn(), kill: jest.fn() } }),
    utils: { toArray: jest.fn(), distribute: jest.fn(), shuffle: jest.fn() },
    defaults: jest.fn(),
  }
  gsapObj.gsap = gsapObj
  return gsapObj
})

jest.mock('@supabase/supabase-js', () => ({
  createClient: jest.fn(function() {
    return {
      auth: {
        signUp: jest.fn(),
        signInWithPassword: jest.fn(),
        signOut: jest.fn(),
        getSession: jest.fn().mockResolvedValue({ data: { session: null }, error: null }),
        onAuthStateChange: jest.fn(function() { return { data: { subscription: { unsubscribe: jest.fn() } } } }),
      },
      from: jest.fn(function() {
        return {
          select: jest.fn().mockReturnThis(),
          insert: jest.fn().mockReturnThis(),
          update: jest.fn().mockReturnThis(),
          delete: jest.fn().mockReturnThis(),
          eq: jest.fn().mockReturnThis(),
          single: jest.fn(),
          order: jest.fn().mockReturnThis(),
          limit: jest.fn().mockReturnThis(),
        }
      }),
      rpc: jest.fn(),
    }
  }),
}))

jest.mock('posthog-js', () => ({
  init: jest.fn(),
  capture: jest.fn(),
  identify: jest.fn(),
  reset: jest.fn(),
  get_distinct_id: jest.fn(function() { return 'test-id' }),
  opt_in_capturing: jest.fn(),
  opt_out_capturing: jest.fn(),
  has_opted_in_capturing: jest.fn(function() { return false }),
  has_opted_out_capturing: jest.fn(function() { return false }),
}))

jest.mock('next-view-transitions', () => ({
  Link: function MockLink(props) {
    var NextLink = require('next/link').default
    var React = require('react')
    return React.createElement(NextLink, Object.assign({ href: '#' }, props), props.children)
  },
}))

jest.mock('sonner', () => ({
  toast: {
    success: jest.fn(),
    error: jest.fn(),
    info: jest.fn(),
    warning: jest.fn(),
    custom: jest.fn(),
  },
  Toaster: jest.fn(function() { return null }),
}))

jest.mock('lenis', () => {
  var Lenis = jest.fn(function() {
    return {
      on: jest.fn(),
      destroy: jest.fn(),
      raf: jest.fn(),
      scrollTo: jest.fn(),
    }
  })
  return { default: Lenis, useLenis: jest.fn() }
})

jest.mock('@react-three/fiber', () => ({
  Canvas: function MockCanvas(props) { return null },
  useFrame: jest.fn(),
  useThree: jest.fn(function() { return { scene: {}, camera: {}, gl: {} } }),
  extend: jest.fn(),
}))

jest.mock('@react-three/drei', () => ({
  OrbitControls: jest.fn(function() { return null }),
  Float: function MockFloat(props) { return null },
  MeshDistortMaterial: jest.fn(function() { return null }),
  MeshWobbleMaterial: jest.fn(function() { return null }),
  Environment: jest.fn(function() { return null }),
}))

// ── i18n mock (used by all components) ──────────────────────────────

jest.mock('react-i18next', () => ({
  useTranslation: function() {
    var translations = {
      'connecting_warming': 'Connecting... (~30 seconds on first load)',
      'common.install_title': 'Install SafeVixAI',
      'common.install_desc': 'Get offline access & faster loading',
      'common.install_btn': 'Install',
      'common.dismiss_install': 'Dismiss install prompt',
      'nav.home': 'Home',
      'nav.emergency': 'Emergency',
      'nav.sos': 'SOS',
      'nav.challan': 'Challan',
      'nav.profile': 'Profile',
      'nav.settings': 'Settings',
      'nav.assistant': 'Assistant',
      'nav.report': 'Report',
      'nav.tracking': 'Tracking',
      'nav.offline': 'Offline',
      'nav.locator': 'Locator',
      'nav.guide': 'Guide',
    }
    return {
      t: function(key, fallback) { return translations[key] || (typeof fallback === 'string' ? fallback : key) },
      i18n: { changeLanguage: function() { return Promise.resolve() }, language: 'en' },
    }
  },
  initReactI18next: { type: '3rdParty', init: function() {} },
}))

// ── Service Worker / Fetch API polyfills for JSDOM ───────────

if (typeof globalThis.Response === 'undefined') {
  globalThis.Response = function(body, init) {
    init = init || {}
    this.body = body
    this.status = init.status || 200
    this.ok = this.status >= 200 && this.status < 300
    this.headers = init.headers || {}
    this._bodyText = typeof body === 'string' ? body : ''
  }
  globalThis.Response.prototype.clone = function() {
    return new globalThis.Response(this._bodyText, { status: this.status, headers: this.headers })
  }
  globalThis.Response.prototype.text = function() {
    return Promise.resolve(this._bodyText)
  }
  globalThis.Response.prototype.json = function() {
    return Promise.resolve(JSON.parse(this._bodyText))
  }
}

if (typeof globalThis.Request === 'undefined') {
  globalThis.Request = function(input, init) {
    init = init || {}
    this.url = typeof input === 'string' ? input : input.url || ''
    this.method = (init.method || 'GET').toUpperCase()
    this.headers = init.headers || {}
    this.mode = init.mode || 'cors'
  }
  globalThis.Request.prototype.clone = function() {
    return new globalThis.Request(this.url, { method: this.method, headers: this.headers })
  }
}

if (typeof globalThis.Headers === 'undefined') {
  globalThis.Headers = function(init) {
    this._map = {}
    if (init) { Object.assign(this._map, init) }
  }
  globalThis.Headers.prototype.get = function(k) { return this._map[k] || null }
  globalThis.Headers.prototype.set = function(k, v) { this._map[k] = v }
  globalThis.Headers.prototype.has = function(k) { return k in this._map }
}

if (typeof globalThis.PushEvent === 'undefined') {
  globalThis.PushEvent = function(type, init) {
    this.type = type
    this.data = (init && init.data) ? init.data : null
  }
}

// ── Polyfills for test environment ────────────────────────────

if (typeof globalThis.TextEncoder === 'undefined') {
  globalThis.TextEncoder = require('util').TextEncoder
  globalThis.TextDecoder = require('util').TextDecoder
}

var originalWarn = console.warn
var originalError = console.error

beforeAll(function() {
  console.warn = jest.fn()
  console.error = jest.fn()
})

afterAll(function() {
  console.warn = originalWarn
  console.error = originalError
})
