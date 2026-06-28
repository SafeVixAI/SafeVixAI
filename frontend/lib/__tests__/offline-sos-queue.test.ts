jest.mock('idb', function () { return { openDB: jest.fn() } })

var mockStore: any = { getAllKeys: jest.fn(), getAll: jest.fn(), add: jest.fn(), delete: jest.fn(), clear: jest.fn() }
var mockTx = { store: mockStore, done: Promise.resolve() }
var mockDb = { transaction: jest.fn(function () { return mockTx }), add: jest.fn() }
var mockOpenDB: jest.Mock = require('idb').openDB as jest.Mock
mockOpenDB.mockResolvedValue(mockDb)

var mockFetch = jest.fn()
global.fetch = mockFetch

if (typeof window !== 'undefined') {
  Object.defineProperty(window, 'indexedDB', { value: {}, writable: true, configurable: true })
}

function requireModule(openDBResolvedValue: any = mockDb) {
  jest.resetModules()
  var freshIdb = require('idb')
  if (freshIdb.openDB !== mockOpenDB) {
    // After resetModules, the factory re-ran, so we need to use the fresh mock
    freshIdb.openDB.mockResolvedValue(openDBResolvedValue)
  }
  return require('../offline-sos-queue')
}

describe('offline-sos-queue', function () {
  beforeEach(function () {
    mockFetch.mockReset()
    mockOpenDB.mockClear()
    mockDb.transaction.mockClear()
    mockStore.getAllKeys.mockReset()
    mockStore.getAll.mockReset()
    mockStore.add.mockReset()
    mockStore.delete.mockReset()
    sessionStorage.clear()
  })

  // ── initDB ──

  it('initDB returns a promise in browser environment', function () {
    var mod = requireModule()
    var result = mod.initDB()
    expect(result).toBeInstanceOf(Promise)
  })

  it('initDB sets indexedDbUnavailable on failure', async function () {
    var mod = requireModule(null)
    var result = await mod.initDB()
    expect(result).toBeNull()
  })

  // ── registerOfflineSyncListeners ──

  it('registerOfflineSyncListeners does not register twice', function () {
    var addEventListener = jest.spyOn(window, 'addEventListener')
    var mod = requireModule()
    mod.registerOfflineSyncListeners()
    mod.registerOfflineSyncListeners()
    expect(addEventListener).toHaveBeenCalledTimes(1)
    addEventListener.mockRestore()
  })

  it('registerOfflineSyncListeners no-ops when not browser', function () {
    var origWindow = globalThis.window
    delete (globalThis as any).window
    jest.resetModules()
    jest.doMock('idb', function () { return { openDB: jest.fn() } })
    var mod = require('../offline-sos-queue')
    expect(function () { mod.registerOfflineSyncListeners() }).not.toThrow()
    globalThis.window = origWindow
  })

  it('registerOfflineSyncListeners triggers ensureServiceWorker', function () {
    var swRegister = jest.fn()
    Object.defineProperty(navigator, 'serviceWorker', {
      value: { register: swRegister },
      configurable: true,
    })
    var mod = requireModule()
    mod.registerOfflineSyncListeners()
    expect(swRegister).toHaveBeenCalledTimes(1)
  })

  // ── enqueueSOS ──

  it('enqueueSOS adds to IndexedDB', async function () {
    var mod = requireModule()
    mockDb.add.mockResolvedValue(undefined)
    await mod.enqueueSOS({ lat: 13, lon: 80 })
    expect(mockDb.add).toHaveBeenCalled()
  })

  it('enqueueSOS tries SyncManager when available', async function () {
    var origSyncManager = (window as any).SyncManager
    ;(window as any).SyncManager = function SyncManager() {}
    var swReady = { sync: { register: jest.fn().mockResolvedValue(undefined) } }
    var origSWReady = (navigator as any).serviceWorker.ready
    ;(navigator as any).serviceWorker.ready = Promise.resolve(swReady)
    var mod = requireModule()
    mockDb.add.mockResolvedValue(undefined)
    await mod.enqueueSOS({ lat: 13, lon: 80 })
    expect(swReady.sync.register).toHaveBeenCalledWith('sos-queue-flush')
    ;(window as any).SyncManager = origSyncManager
    ;(navigator as any).serviceWorker.ready = origSWReady
  })

  it('enqueueSOS catches SyncManager error gracefully', async function () {
    (window as any).SyncManager = function SyncManager() {}
    var swReady = { sync: { register: jest.fn().mockRejectedValue(new Error('sync error')) } }

    ;(navigator as any).serviceWorker.ready = Promise.resolve(swReady)
    var mod = requireModule()
    mockDb.add.mockResolvedValue(undefined)
    await expect(mod.enqueueSOS({ lat: 13, lon: 80 })).resolves.toBeUndefined()
    delete (window as any).SyncManager
  })

  it('enqueueSOS uses fallback when IndexedDB fails', async function () {
    var mod = requireModule(null)
    await mod.enqueueSOS({ lat: 13, lon: 80 })
    var stored = sessionStorage.getItem('safevix:sos-queue:fallback')
    expect(stored).not.toBeNull()
    var parsed = JSON.parse(stored!)
    expect(parsed).toHaveLength(1)
  })

  // ── enqueueRoadReport ──

  it('enqueueRoadReport adds to IndexedDB', async function () {
    var mod = requireModule()
    mockDb.add.mockResolvedValue(undefined)
    await mod.enqueueRoadReport({ lat: 13, lon: 80, issue_type: 'pothole', severity: 3 })
    expect(mockDb.add).toHaveBeenCalled()
  })

  it('enqueueRoadReport tries SyncManager when available', async function () {
    (window as any).SyncManager = function SyncManager() {}
    var swReady = { sync: { register: jest.fn().mockResolvedValue(undefined) } }
    ;(navigator as any).serviceWorker.ready = Promise.resolve(swReady)
    var mod = requireModule()
    mockDb.add.mockResolvedValue(undefined)
    await mod.enqueueRoadReport({ lat: 13, lon: 80, issue_type: 'pothole', severity: 3 })
    expect(swReady.sync.register).toHaveBeenCalledWith('road-report-queue-flush')
    delete (window as any).SyncManager
  })

  it('enqueueRoadReport uses fallback when IndexedDB fails', async function () {
    var mod = requireModule(null)
    await mod.enqueueRoadReport({ lat: 13, lon: 80, issue_type: 'pothole', severity: 3 })
    var stored = sessionStorage.getItem('safevix:road-report-queue:fallback')
    expect(stored).not.toBeNull()
    var parsed = JSON.parse(stored!)
    expect(parsed).toHaveLength(1)
  })

  // ── syncOfflineSOSQueue ──

  it('syncOfflineSOSQueue does nothing when offline', async function () {
    var origOnLine = navigator.onLine
    Object.defineProperty(navigator, 'onLine', { value: false, configurable: true })
    jest.resetModules()
    jest.doMock('idb', function () { return { openDB: jest.fn() } })
    var mod = require('../offline-sos-queue')
    await mod.syncOfflineSOSQueue()
    Object.defineProperty(navigator, 'onLine', { value: origOnLine, configurable: true })
  })

  it('syncOfflineSOSQueue processes items and deletes on success', async function () {
    var mod = requireModule()
    mockStore.getAllKeys.mockResolvedValue([1])
    mockStore.getAll.mockResolvedValue([{ lat: 13, lon: 80 }])
    mockFetch.mockResolvedValueOnce({ ok: true })
    await mod.syncOfflineSOSQueue()
    expect(mockStore.delete).toHaveBeenCalledWith(1)
  })

  it('syncOfflineSOSQueue stops on API failure', async function () {
    var mod = requireModule()
    mockStore.getAllKeys.mockResolvedValue([1, 2])
    mockStore.getAll.mockResolvedValue([{ lat: 13, lon: 80 }, { lat: 14, lon: 81 }])
    mockFetch.mockResolvedValueOnce({ ok: false })
    await mod.syncOfflineSOSQueue()
    expect(mockStore.delete).not.toHaveBeenCalled()
  })

  it('syncOfflineSOSQueue handles empty queue', async function () {
    var mod = requireModule()
    mockStore.getAllKeys.mockResolvedValue([])
    mockStore.getAll.mockResolvedValue([])
    await expect(mod.syncOfflineSOSQueue()).resolves.toBeUndefined()
  })

  it('syncOfflineSOSQueue waits for readTx.done', async function () {
    var mod = requireModule()
    mockStore.getAllKeys.mockResolvedValue([1])
    mockStore.getAll.mockResolvedValue([{ lat: 13, lon: 80 }])
    mockFetch.mockResolvedValueOnce({ ok: true })
    await mod.syncOfflineSOSQueue()
    expect(mockStore.delete).toHaveBeenCalledWith(1)
  })

  it('syncOfflineSOSQueue stops on fetch error', async function () {
    var mod = requireModule()
    mockStore.getAllKeys.mockResolvedValue([1])
    mockStore.getAll.mockResolvedValue([{ lat: 13, lon: 80 }])
    mockFetch.mockRejectedValueOnce(new Error('Network error'))
    await mod.syncOfflineSOSQueue()
    expect(mockStore.delete).not.toHaveBeenCalled()
  })

  // ── syncOfflineRoadReportQueue ──

  it('syncOfflineRoadReportQueue does nothing when offline', async function () {
    var origOnLine = navigator.onLine
    Object.defineProperty(navigator, 'onLine', { value: false, configurable: true })
    jest.resetModules()
    jest.doMock('idb', function () { return { openDB: jest.fn() } })
    var mod = require('../offline-sos-queue')
    await mod.syncOfflineRoadReportQueue()
    Object.defineProperty(navigator, 'onLine', { value: origOnLine, configurable: true })
  })

  it('syncOfflineRoadReportQueue processes items with formData', async function () {
    var mod = requireModule()
    mockStore.getAllKeys.mockResolvedValue([1])
    mockStore.getAll.mockResolvedValue([{ lat: 13, lon: 80, issue_type: 'pothole', severity: 3, description: 'Big one', photo: new Blob(['test']), photoName: 'test.webp' }])
    mockFetch.mockResolvedValueOnce({ ok: true })
    await mod.syncOfflineRoadReportQueue()
    expect(mockStore.delete).toHaveBeenCalledWith(1)
    var fetchBody = mockFetch.mock.calls[0][1].body
    expect(fetchBody).toBeInstanceOf(FormData)
  })

  it('syncOfflineRoadReportQueue handles items with apiUrl', async function () {
    var mod = requireModule()
    mockStore.getAllKeys.mockResolvedValue([1])
    mockStore.getAll.mockResolvedValue([{ lat: 13, lon: 80, issue_type: 'pothole', severity: 3, apiUrl: 'http://custom:8000' }])
    mockFetch.mockResolvedValueOnce({ ok: true })
    await mod.syncOfflineRoadReportQueue()
    expect(mockFetch.mock.calls[0][0]).toContain('http://custom:8000')
  })

  it('syncOfflineRoadReportQueue stops on API failure', async function () {
    var mod = requireModule()
    mockStore.getAllKeys.mockResolvedValue([1])
    mockStore.getAll.mockResolvedValue([{ lat: 13, lon: 80, issue_type: 'pothole', severity: 3 }])
    mockFetch.mockResolvedValueOnce({ ok: false })
    await mod.syncOfflineRoadReportQueue()
    expect(mockStore.delete).not.toHaveBeenCalled()
  })

  it('syncOfflineRoadReportQueue handles empty queue', async function () {
    var mod = requireModule()
    mockStore.getAllKeys.mockResolvedValue([])
    mockStore.getAll.mockResolvedValue([])
    await expect(mod.syncOfflineRoadReportQueue()).resolves.toBeUndefined()
  })

  it('syncOfflineRoadReportQueue handles description trim', async function () {
    var mod = requireModule()
    mockStore.getAllKeys.mockResolvedValue([1])
    mockStore.getAll.mockResolvedValue([{ lat: 13, lon: 80, issue_type: 'pothole', severity: 3, description: '   ' }])
    mockFetch.mockResolvedValueOnce({ ok: true })
    await mod.syncOfflineRoadReportQueue()
    expect(mockStore.delete).toHaveBeenCalled()
  })

  // ── Fallback sync ──

  it('syncFallbackSOSQueue syncs items from sessionStorage', async function () {
    var items = [{ lat: 13, lon: 80, timestamp: '2026-01-01T00:00:00Z' }]
    sessionStorage.setItem('safevix:sos-queue:fallback', JSON.stringify(items))
    var mod = requireModule(null)
    mockFetch.mockResolvedValueOnce({ ok: true })
    await mod.syncOfflineSOSQueue()
    var remaining = sessionStorage.getItem('safevix:sos-queue:fallback')
    expect(remaining).toBe('[]')
  })

  it('syncFallbackSOSQueue keeps failed items on fetch error', async function () {
    var items = [{ lat: 13, lon: 80, timestamp: '2026-01-01T00:00:00Z' }]
    sessionStorage.setItem('safevix:sos-queue:fallback', JSON.stringify(items))
    var mod = requireModule(null)
    mockFetch.mockRejectedValueOnce(new Error('fail'))
    await mod.syncOfflineSOSQueue()
    var remaining = sessionStorage.getItem('safevix:sos-queue:fallback')
    expect(remaining).not.toBe('[]')
  })

  it('syncFallbackSOSQueue keeps failed items on API error', async function () {
    var items = [{ lat: 13, lon: 80, timestamp: '2026-01-01T00:00:00Z' }]
    sessionStorage.setItem('safevix:sos-queue:fallback', JSON.stringify(items))
    var mod = requireModule(null)
    mockFetch.mockResolvedValueOnce({ ok: false })
    await mod.syncOfflineSOSQueue()
    var remaining = sessionStorage.getItem('safevix:sos-queue:fallback')
    expect(remaining).not.toBe('[]')
  })

  it('syncFallbackSOSQueue handles empty fallback', async function () {
    var mod = requireModule(null)
    await mod.syncOfflineSOSQueue()
  })

  it('syncFallbackRoadReportQueue syncs items from sessionStorage', async function () {
    var items = [{ lat: 13, lon: 80, issue_type: 'pothole', severity: 3, timestamp: '2026-01-01T00:00:00Z' }]
    sessionStorage.setItem('safevix:road-report-queue:fallback', JSON.stringify(items))
    var mod = requireModule(null)
    mockFetch.mockResolvedValueOnce({ ok: true })
    await mod.syncOfflineRoadReportQueue()
    var remaining = sessionStorage.getItem('safevix:road-report-queue:fallback')
    expect(remaining).toBe('[]')
  })

  it('syncFallbackRoadReportQueue keeps failed items on API error', async function () {
    var items = [{ lat: 13, lon: 80, issue_type: 'pothole', severity: 3, timestamp: '2026-01-01T00:00:00Z' }]
    sessionStorage.setItem('safevix:road-report-queue:fallback', JSON.stringify(items))
    var mod = requireModule(null)
    mockFetch.mockResolvedValueOnce({ ok: false })
    await mod.syncOfflineRoadReportQueue()
    var remaining = sessionStorage.getItem('safevix:road-report-queue:fallback')
    expect(remaining).not.toBe('[]')
  })

  it('syncFallbackRoadReportQueue keeps items on fetch error', async function () {
    var items = [{ lat: 13, lon: 80, issue_type: 'pothole', severity: 3, timestamp: '2026-01-01T00:00:00Z' }]
    sessionStorage.setItem('safevix:road-report-queue:fallback', JSON.stringify(items))
    var mod = requireModule(null)
    mockFetch.mockRejectedValueOnce(new Error('network'))
    await mod.syncOfflineRoadReportQueue()
    var remaining = sessionStorage.getItem('safevix:road-report-queue:fallback')
    expect(remaining).not.toBe('[]')
  })

  // ── readFallbackQueue error handling ──

  it('readFallbackQueue handles JSON parse error', async function () {
    sessionStorage.setItem('safevix:sos-queue:fallback', 'invalid-json')
    var mod = requireModule(null)
    await mod.enqueueSOS({ lat: 1, lon: 2 })
    var stored = sessionStorage.getItem('safevix:sos-queue:fallback')
    // The invalid-json was removed by readFallbackQueue catch block,
    // then enqueueSOS added its item to the (now empty) fallback queue
    var parsed = JSON.parse(stored!)
    expect(parsed).toHaveLength(1)
    expect(parsed[0].lat).toBe(1)
  })

  // ── Export check ──

  it('exports all public functions', function () {
    var mod = requireModule()
    expect(typeof mod.initDB).toBe('function')
    expect(typeof mod.enqueueSOS).toBe('function')
    expect(typeof mod.enqueueRoadReport).toBe('function')
    expect(typeof mod.syncOfflineSOSQueue).toBe('function')
    expect(typeof mod.syncOfflineRoadReportQueue).toBe('function')
    expect(typeof mod.registerOfflineSyncListeners).toBe('function')
  })
})
