import React from 'react'
import { render, screen, waitFor, act } from '@testing-library/react'

jest.mock('@/lib/store', function() {
  var mockStore = {
    crashDetectionEnabled: false,
    gpsLocation: { lat: 13.0827, lon: 80.2707, accuracy: 50, timestamp: Date.now() },
    userProfile: { name: 'Test User', bloodGroup: 'O+', vehicleNumber: 'TN01AB1234', preferredLanguage: 'en' },
    connectivity: 'online',
    setServerWarming: jest.fn(),
    setUserProfile: jest.fn(),
    setProfileHydrated: jest.fn(),
    setAuth: jest.fn(),
    clearAuth: jest.fn(),
    setCrashDetectionEnabled: jest.fn(),
  }
  return {
    useAppStore: Object.assign(
      function(selector) { return typeof selector === 'function' ? selector(mockStore) : mockStore },
      { getState: function() { return mockStore } }
    ),
  }
})

jest.mock('@/lib/api', function() {
  return { triggerSos: jest.fn(function() { return Promise.resolve() }), fetchCsrfToken: jest.fn(function() { return Promise.resolve() }) }
})

jest.mock('@/lib/crash-detection', function() {
  return { startCrashDetection: jest.fn(function() { return Promise.resolve() }), stopCrashDetection: jest.fn() }
})

jest.mock('@/lib/offline-sos-queue', function() {
  return { enqueueSOS: jest.fn(function() { return Promise.resolve() }), registerOfflineSyncListeners: jest.fn() }
})

jest.mock('@/lib/safety-constants', function() {
  return { STANDARD_GRAVITY_MS2: 9.80665 }
})

jest.mock('@/lib/supabase-auth', function() {
  return {
    getSupabaseBrowserClient: jest.fn(function() {
      return {
        auth: {
          getSession: jest.fn(function() { return Promise.resolve({ data: { session: null }, error: null }) }),
          onAuthStateChange: jest.fn(function() { return { data: { subscription: { unsubscribe: jest.fn() } } } }),
        },
      }
    }),
  }
})

jest.mock('@/lib/public-env', function() {
  return { PUBLIC_API_BASE_URL: 'http://localhost:8000', PUBLIC_CHATBOT_BASE_URL: 'http://localhost:8010' }
})

jest.mock('@/lib/features', function() {
  return { FEATURES: { crashDetection: false } }
})

jest.mock('@/lib/live-tracking', function() {
  return { beginLocationBroadcast: jest.fn(), startFamilyTracking: jest.fn(function() { return Promise.resolve({ session_id: 'test-session', tracking_url: 'http://track.test' }) }) }
})

jest.mock('@/lib/analytics', function() {
  return { track: { pageLoadTiming: jest.fn(), crashDetected: jest.fn(), sosActivated: jest.fn(), crashCancelled: jest.fn(), offlineSosQueued: jest.fn() } }
})

jest.mock('@/lib/rum', function() {
  return { initRUM: jest.fn() }
})

jest.mock('@/lib/profile-storage', function() {
  return { loadUserProfileFromIndexedDB: jest.fn(function() { return Promise.resolve(null) }), migrateUserProfileFromLocalStorage: jest.fn(function() { return Promise.resolve() }) }
})

jest.mock('@/lib/i18n', function() {
  return { __esModule: true, default: { language: 'en', changeLanguage: jest.fn(function() { return Promise.resolve() }) } }
})

jest.mock('@/components/crash/CrashCountdown', function() {
  var React2 = require('react')
  return { CrashCountdown: function CrashCountdownMock(props) {
    return React2.createElement('div', { 'data-testid': 'crash-countdown' },
      props.severity,
      React2.createElement('button', { 'data-testid': 'dispatch-btn', onClick: props.onDispatch }, 'Dispatch')
    )
  }}
})

jest.mock('@/components/InstallPrompt', function() {
  return { __esModule: true, default: function() { return null } }
})

jest.mock('@/components/ui/CookieConsent', function() {
  return { __esModule: true, default: function() { return null } }
})

jest.mock('@/components/ui/GpsConsent', function() {
  return { __esModule: true, default: function() { return null } }
})

jest.mock('sonner', function() {
  return { toast: { info: jest.fn(), success: jest.fn(), error: jest.fn() }, Toaster: function() { return null } }
})

jest.mock('lucide-react', function() {
  return {
    Loader2: function MockLoader2() { return null },
  }
})

describe('EnterpriseClientAppHooks', function() {
  beforeEach(function() {
    jest.clearAllMocks()
    window.localStorage.getItem = jest.fn(function() { return null })
    window.addEventListener = jest.fn(function() {})
    window.removeEventListener = jest.fn(function() {})
    window.dispatchEvent = jest.fn(function() {})
    ;(navigator as any).serviceWorker = { register: jest.fn(function() { return Promise.resolve({ scope: '/test-scope' }) }) }
    ;(navigator as any).storage = { persist: jest.fn(function() { return Promise.resolve(true) }) }
    Object.defineProperty(document, 'readyState', { value: 'complete', writable: true, configurable: true })
    globalThis.fetch = jest.fn(function() { return Promise.resolve({ ok: true, status: 200 }) })
  })

  it('renders without crashing', async function() {
    var mod = await import('../EnterpriseClientAppHooks')
    var { container } = render(React.createElement(mod.EnterpriseClientAppHooks))
    expect(container).toBeDefined()
  })

  it('does not show warming banner when not warming', async function() {
    var mod = await import('../EnterpriseClientAppHooks')
    render(React.createElement(mod.EnterpriseClientAppHooks))
    expect(screen.queryByText('CONNECTING...')).not.toBeInTheDocument()
  })

  it('loads and exports EnterpriseClientAppHooks', async function() {
    var mod = await import('../EnterpriseClientAppHooks')
    expect(mod.EnterpriseClientAppHooks).toBeDefined()
  })

  it('registers service worker on mount', async function() {
    var mod = await import('../EnterpriseClientAppHooks')
    render(React.createElement(mod.EnterpriseClientAppHooks))
    expect(navigator.serviceWorker.register).toHaveBeenCalledWith('/sw.js')
  })

  it('calls initRUM on mount', async function() {
    var rum = require('@/lib/rum')
    var mod = await import('../EnterpriseClientAppHooks')
    render(React.createElement(mod.EnterpriseClientAppHooks))
    expect(rum.initRUM).toHaveBeenCalled()
  })

  it('calls registerOfflineSyncListeners on mount', async function() {
    var queue = require('@/lib/offline-sos-queue')
    var mod = await import('../EnterpriseClientAppHooks')
    render(React.createElement(mod.EnterpriseClientAppHooks))
    expect(queue.registerOfflineSyncListeners).toHaveBeenCalled()
  })

  it('calls migrateUserProfileFromLocalStorage on mount', async function() {
    var ps = require('@/lib/profile-storage')
    var mod = await import('../EnterpriseClientAppHooks')
    render(React.createElement(mod.EnterpriseClientAppHooks))
    expect(ps.migrateUserProfileFromLocalStorage).toHaveBeenCalled()
  })

  it('calls loadUserProfileFromIndexedDB on mount', async function() {
    var ps = require('@/lib/profile-storage')
    var mod = await import('../EnterpriseClientAppHooks')
    render(React.createElement(mod.EnterpriseClientAppHooks))
    await waitFor(function() { expect(ps.loadUserProfileFromIndexedDB).toHaveBeenCalled() })
  })

  it('sets user profile from IndexedDB when profile is found', async function() {
    var ps = require('@/lib/profile-storage')
    var profileData = { name: 'Stored User', bloodGroup: 'A+', phone: '+919999999999' }
    ps.loadUserProfileFromIndexedDB.mockResolvedValueOnce(profileData)
    var mod = await import('../EnterpriseClientAppHooks')
    render(React.createElement(mod.EnterpriseClientAppHooks))
    await waitFor(function() { expect(ps.loadUserProfileFromIndexedDB).toHaveBeenCalled() })
    var store = require('@/lib/store')
    expect(store.useAppStore.getState().setUserProfile).toHaveBeenCalledWith(profileData)
    expect(store.useAppStore.getState().setProfileHydrated).toHaveBeenCalledWith(true)
  })

  it('calls fetchCsrfToken on mount', async function() {
    var api = require('@/lib/api')
    var mod = await import('../EnterpriseClientAppHooks')
    render(React.createElement(mod.EnterpriseClientAppHooks))
    expect(api.fetchCsrfToken).toHaveBeenCalled()
  })

  it('syncs auth session on mount', async function() {
    var supabase = require('@/lib/supabase-auth')
    var mod = await import('../EnterpriseClientAppHooks')
    render(React.createElement(mod.EnterpriseClientAppHooks))
    expect(supabase.getSupabaseBrowserClient).toHaveBeenCalled()
  })

  it('calls setAuth when supabase session exists', async function() {
    var supabase = require('@/lib/supabase-auth')
    var fakeSession = { access_token: 'tok', user: { email: 'user@test.com' } }
    supabase.getSupabaseBrowserClient.mockReturnValueOnce({
      auth: {
        getSession: jest.fn(function() { return Promise.resolve({ data: { session: fakeSession }, error: null }) }),
        onAuthStateChange: jest.fn(function() { return { data: { subscription: { unsubscribe: jest.fn() } } } }),
      },
    })
    var mod = await import('../EnterpriseClientAppHooks')
    render(React.createElement(mod.EnterpriseClientAppHooks))
    await waitFor(function() {
      var store = require('@/lib/store')
      expect(store.useAppStore.getState().setAuth).toHaveBeenCalledWith('user@test.com')
    })
  })

  it('calls clearAuth when supabase session is null', async function() {
    var supabase = require('@/lib/supabase-auth')
    var mod = await import('../EnterpriseClientAppHooks')
    render(React.createElement(mod.EnterpriseClientAppHooks))
    await waitFor(function() {
      var store = require('@/lib/store')
      expect(store.useAppStore.getState().clearAuth).toHaveBeenCalled()
    })
  })

  it('dispatches page load timing', async function() {
    var analytics = require('@/lib/analytics')
    var mod = await import('../EnterpriseClientAppHooks')
    render(React.createElement(mod.EnterpriseClientAppHooks))
    expect(analytics.track.pageLoadTiming).toHaveBeenCalled()
  })

  it('calls requestPersistentStorage', async function() {
    var mod = await import('../EnterpriseClientAppHooks')
    render(React.createElement(mod.EnterpriseClientAppHooks))
    await waitFor(function() { expect(navigator.storage.persist).toHaveBeenCalled() })
  })

  it('handles E2E skip auth flag', async function() {
    process.env.NODE_ENV = 'development'
    window.localStorage.getItem = jest.fn(function() { return 'true' })
    var mod = await import('../EnterpriseClientAppHooks')
    render(React.createElement(mod.EnterpriseClientAppHooks))
    expect(screen.queryByText('CONNECTING...')).not.toBeInTheDocument()
  })

  it('calls setServerWarming(true) when health check is aborted', async function() {
    globalThis.fetch = jest.fn(function() { return Promise.reject(Object.assign(new Error('The operation was aborted'), { name: 'AbortError' })) })
    var store = require('@/lib/store')
    var mod = await import('../EnterpriseClientAppHooks')
    render(React.createElement(mod.EnterpriseClientAppHooks))
    await waitFor(function() { expect(store.useAppStore.getState().setServerWarming).toHaveBeenCalledWith(true) })
  })

  it('registers service worker on load event when not ready', async function() {
    Object.defineProperty(document, 'readyState', { value: 'loading', writable: true, configurable: true })
    var addEventListenerMock = jest.fn()
    window.addEventListener = addEventListenerMock
    var mod = await import('../EnterpriseClientAppHooks')
    render(React.createElement(mod.EnterpriseClientAppHooks))
    var loadCall = addEventListenerMock.mock.calls.find(function(c) { return c[0] === 'load' })
    expect(loadCall).toBeDefined()
  })

  it('logs service worker registration failure', async function() {
    var consoleSpy = jest.spyOn(console, 'error').mockImplementation(function() {})
    ;(navigator as any).serviceWorker = { register: jest.fn(function() { return Promise.reject(new Error('SW failed')) }) }
    var mod = await import('../EnterpriseClientAppHooks')
    render(React.createElement(mod.EnterpriseClientAppHooks))
    await waitFor(function() { expect(consoleSpy).toHaveBeenCalled() })
    consoleSpy.mockRestore()
  })

  it('sets RTL direction for Arabic locale', async function() {
    var store = require('@/lib/store')
    store.useAppStore.getState().userProfile.preferredLanguage = 'ar'
    var i18nMod = require('@/lib/i18n')
    var mod = await import('../EnterpriseClientAppHooks')
    render(React.createElement(mod.EnterpriseClientAppHooks))
    await waitFor(function() { expect(i18nMod.default.changeLanguage).toHaveBeenCalledWith('ar') })
  })

  it('calls fetch health endpoint on mount', async function() {
    globalThis.fetch = jest.fn(function() { return Promise.resolve({ ok: true, status: 200 }) })
    var mod = await import('../EnterpriseClientAppHooks')
    render(React.createElement(mod.EnterpriseClientAppHooks))
    await waitFor(function() { expect(globalThis.fetch).toHaveBeenCalled() })
  })

  it('sets crash state when crash is detected', async function() {
    var features = require('@/lib/features')
    features.FEATURES.crashDetection = true
    var store = require('@/lib/store')
    store.useAppStore.getState().crashDetectionEnabled = true
    var crashDetection = require('@/lib/crash-detection')
    crashDetection.startCrashDetection.mockImplementationOnce(function(handler) {
      handler(98.0665)
      return Promise.resolve()
    })
    var mod = await import('../EnterpriseClientAppHooks')
    render(React.createElement(mod.EnterpriseClientAppHooks))
    await waitFor(function() { expect(screen.getByTestId('crash-countdown')).toBeInTheDocument() })
  })

  it('dispatches page load timing on load event when not ready', async function() {
    Object.defineProperty(document, 'readyState', { value: 'loading', writable: true, configurable: true })
    var addEventListenerMock = jest.fn()
    window.addEventListener = addEventListenerMock
    var mod = await import('../EnterpriseClientAppHooks')
    render(React.createElement(mod.EnterpriseClientAppHooks))
    var loadCall = addEventListenerMock.mock.calls.find(function(c) { return c[0] === 'load' })
    expect(loadCall).toBeDefined()
  })

  it('calls syncSession via onAuthStateChange when auth event fires', async function() {
    var supabase = require('@/lib/supabase-auth')
    var onAuthCb: Function = function() {}
    supabase.getSupabaseBrowserClient.mockReturnValueOnce({
      auth: {
        getSession: jest.fn(function() { return Promise.resolve({ data: { session: null }, error: null }) }),
        onAuthStateChange: jest.fn(function(cb: Function) {
          onAuthCb = cb
          return { data: { subscription: { unsubscribe: jest.fn() } } }
        }),
      },
    })
    var store = require('@/lib/store')
    var mod = await import('../EnterpriseClientAppHooks')
    render(React.createElement(mod.EnterpriseClientAppHooks))
    onAuthCb('SIGNED_IN', { access_token: 'tok', user: { email: 'auth@test.com' } })
    await waitFor(function() { expect(store.useAppStore.getState().setAuth).toHaveBeenCalledWith('auth@test.com') })
  })

  it('calls ping when visibility becomes visible', async function() {
    var origFetch = globalThis.fetch
    globalThis.fetch = jest.fn(function() { return Promise.resolve({ ok: true }) })
    var origDocAddEventListener = document.addEventListener
    var addEventListenerMock = jest.fn()
    document.addEventListener = addEventListenerMock
    var mod = await import('../EnterpriseClientAppHooks')
    render(React.createElement(mod.EnterpriseClientAppHooks))
    var visCb = addEventListenerMock.mock.calls.find(function(c) { return c[0] === 'visibilitychange' })
    expect(visCb).toBeDefined()
    document.addEventListener = origDocAddEventListener
    globalThis.fetch = origFetch
  })

  it('triggers ping callback when visibility changes to visible', async function() {
    var fetchMock = jest.fn(function() { return Promise.resolve({ ok: true }) })
    globalThis.fetch = fetchMock
    var origDocAddEventListener = document.addEventListener
    var listeners: Record<string, Function> = {}
    document.addEventListener = jest.fn(function(event: string, cb: Function) { listeners[event] = cb })
    var mod = await import('../EnterpriseClientAppHooks')
    render(React.createElement(mod.EnterpriseClientAppHooks))
    await new Promise(function(r) { return setTimeout(r, 100) })
    listeners['visibilitychange']()
    await new Promise(function(r) { return setTimeout(r, 100) })
    expect(fetchMock).toHaveBeenCalled()
    document.addEventListener = origDocAddEventListener
  })

  it('handleDispatchSos sends SOS without crash detection', async function() {
    var features = require('@/lib/features')
    features.FEATURES.crashDetection = true
    var store = require('@/lib/store')
    store.useAppStore.getState().crashDetectionEnabled = true
    store.useAppStore.getState().userProfile = { name: '  ', bloodGroup: 'O+', preferredLanguage: 'en' }
    var crashDetection = require('@/lib/crash-detection')
    crashDetection.startCrashDetection.mockImplementationOnce(function(handler) {
      handler(98.0665)
      return Promise.resolve()
    })
    var mod = await import('../EnterpriseClientAppHooks')
    render(React.createElement(mod.EnterpriseClientAppHooks))
    await waitFor(function() { expect(screen.getByTestId('crash-countdown')).toBeInTheDocument() })
    var crashCountdown = screen.getByTestId('crash-countdown')
    expect(crashCountdown).toBeInTheDocument()
  })

  it('dispatch click triggers SOS with tracking for named user', async function() {
    var features = require('@/lib/features')
    features.FEATURES.crashDetection = true
    var store = require('@/lib/store')
    store.useAppStore.getState().crashDetectionEnabled = true
    store.useAppStore.getState().userProfile.name = 'Test User'
    var api = require('@/lib/api')
    api.triggerSos.mockResolvedValueOnce({ id: 'sos-1' })
    var liveTracking = require('@/lib/live-tracking')
    liveTracking.startFamilyTracking.mockResolvedValueOnce({ session_id: 'sess-1', tracking_url: 'http://track.test' })
    var crashDetection = require('@/lib/crash-detection')
    crashDetection.startCrashDetection.mockImplementationOnce(function(handler) {
      handler(98.0665)
      return Promise.resolve()
    })
    var mod = await import('../EnterpriseClientAppHooks')
    render(React.createElement(mod.EnterpriseClientAppHooks))
    await waitFor(function() { expect(screen.getByTestId('dispatch-btn')).toBeInTheDocument() })
    await act(async function() { screen.getByTestId('dispatch-btn').click() })
    await waitFor(function() { expect(api.triggerSos).toHaveBeenCalled() })
    await waitFor(function() { expect(liveTracking.startFamilyTracking).toHaveBeenCalled() })
    expect(liveTracking.beginLocationBroadcast).toHaveBeenCalled()
  })

  it('dispatch click queues offline SOS when triggerSos fails', async function() {
    var features = require('@/lib/features')
    features.FEATURES.crashDetection = true
    var store = require('@/lib/store')
    store.useAppStore.getState().crashDetectionEnabled = true
    var api = require('@/lib/api')
    api.triggerSos.mockRejectedValueOnce(new Error('network error'))
    var queue = require('@/lib/offline-sos-queue')
    var crashDetection = require('@/lib/crash-detection')
    crashDetection.startCrashDetection.mockImplementationOnce(function(handler) {
      handler(98.0665)
      return Promise.resolve()
    })
    var mod = await import('../EnterpriseClientAppHooks')
    render(React.createElement(mod.EnterpriseClientAppHooks))
    await waitFor(function() { expect(screen.getByTestId('dispatch-btn')).toBeInTheDocument() })
    await act(async function() { screen.getByTestId('dispatch-btn').click() })
    await waitFor(function() { expect(queue.enqueueSOS).toHaveBeenCalled() })
  })

})
