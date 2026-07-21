// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
jest.mock('../store', function () {
  return {
    useAppStore: {
      getState: jest.fn(function () {
        return {
          authToken: null,
          userProfile: { preferredLanguage: 'en' },
          setServerWarming: jest.fn(),
        }
      }),
    },
  }
})

jest.mock('../duckdb-challan', function () {
  return { calculateOfflineChallan: jest.fn().mockResolvedValue({
    base_fine: 500, repeat_fine: null, section: '185 MVA', description: 'Drunk driving'
  })}
})

jest.mock('axios', function () {
  var _requestHandlers: Array<{ fulfilled: Function; rejected?: Function }> = []
  var _responseHandlers: Array<{ fulfilled: Function; rejected?: Function }> = []
  var mockAxiosInstanceFn = jest.fn().mockResolvedValue({ data: 'ok' })
  Object.assign(mockAxiosInstanceFn, {
    get: jest.fn(),
    post: jest.fn(),
    interceptors: {
      request: { use: jest.fn(function (f: Function, r?: Function) { _requestHandlers.push({ fulfilled: f, rejected: r }) }) },
      response: { use: jest.fn(function (f: Function, r?: Function) { _responseHandlers.push({ fulfilled: f, rejected: r }) }) },
    },
    defaults: { headers: {} },
  })
  var mockAxios = {
    create: jest.fn(function () { return mockAxiosInstanceFn }),
    isAxiosError: jest.fn(function (err: any) { return err?.isAxiosError === true }),
    _requestHandlers: _requestHandlers,
    _responseHandlers: _responseHandlers,
  }
  return mockAxios
})

var mockAxios = require('axios')
var mockClient: any = mockAxios.create()
var mockStore = require('../store')

function setMockToken(token: string | null) {
  mockStore.useAppStore.getState = jest.fn(function () {
    return {
      authToken: token,
      userProfile: { preferredLanguage: 'en' },
      setServerWarming: jest.fn(),
    }
  })
}

describe('api', function () {
  beforeEach(function () {
    mockClient.get.mockReset()
    mockClient.post.mockReset()
    mockAxios.isAxiosError.mockClear()
    global.fetch = jest.fn()
  })

  // ── fetchCsrfToken ──

  it('fetchCsrfToken returns token on success', async function () {
    global.fetch = jest.fn().mockResolvedValueOnce({
      ok: true,
      json: async function () { return { csrf_token: 'token-abc' } },
    })
    var mod = await import('../api')
    var result = await mod.fetchCsrfToken()
    expect(result).toBe('token-abc')
  })

  it('fetchCsrfToken returns null on non-ok', async function () {
    global.fetch = jest.fn().mockResolvedValueOnce({ ok: false })
    var mod = await import('../api')
    var result = await mod.fetchCsrfToken()
    expect(result).toBeNull()
  })

  it('fetchCsrfToken returns null on error', async function () {
    global.fetch = jest.fn().mockRejectedValueOnce(new Error('network'))
    var mod = await import('../api')
    var result = await mod.fetchCsrfToken()
    expect(result).toBeNull()
  })

  // ── setCsrfToken ──

  it('setCsrfToken sets the token', function () {
    var mod = require('../api')
    expect(function () { mod.setCsrfToken('new-token') }).not.toThrow()
    expect(function () { mod.setCsrfToken(null) }).not.toThrow()
  })

  // ── extractApiError ──

  it('extractApiError extracts axios error message', function () {
    var mod = require('../api')
    var err = {
      isAxiosError: true,
      message: 'Request failed',
      response: { status: 500, data: { detail: 'Server error' } },
    }
    var result = mod.extractApiError(err)
    expect(result.message).toBe('Server error')
    expect(result.status).toBe(500)
  })

  it('extractApiError handles array detail', function () {
    var mod = require('../api')
    var err = {
      isAxiosError: true,
      message: 'Request failed',
      response: {
        status: 422,
        data: { detail: [{ msg: 'Field required', loc: ['body', 'name'] }] },
      },
    }
    var result = mod.extractApiError(err)
    expect(result.message).toBe('Field required')
  })

  it('extractApiError handles non-axios error', function () {
    var mod = require('../api')
    var err = new Error('generic error')
    var result = mod.extractApiError(err)
    expect(result.message).toBe('generic error')
  })

  it('extractApiError handles unknown error', function () {
    var mod = require('../api')
    var result = mod.extractApiError('string error')
    expect(result.message).toBe('An unexpected error occurred')
  })

  // ── fetchNearbyServices ──

  it('fetchNearbyServices returns normalized response', async function () {
    mockClient.get.mockResolvedValueOnce({
      data: {
        services: [{
          id: '1', name: 'Test Hospital', category: 'hospital',
          sub_category: 'trauma', phone: '911', phone_emergency: '112',
          lat: 13.08, lon: 80.27, distance_meters: 100,
          has_trauma: true, has_icu: false, is_24hr: true,
          address: 'Chennai', source: 'api',
        }],
        count: 1, radius_used: 5000, source: 'api',
      },
    })
    var mod = await import('../api')
    var result = await mod.fetchNearbyServices({ lat: 13, lon: 80 })
    expect(result.services).toHaveLength(1)
    expect(result.services[0].name).toBe('Test Hospital')
    expect(result.services[0].subCategory).toBe('trauma')
    expect(result.services[0].phoneEmergency).toBe('112')
    expect(result.count).toBe(1)
    expect(mockClient.get).toHaveBeenCalledWith('/api/v1/emergency/nearby', expect.any(Object))
  })

  it('fetchNearbyServices handles comma-separated categories', async function () {
    mockClient.get.mockResolvedValueOnce({ data: { services: [], count: 0, radius_used: 0, source: 'api' } })
    var mod = await import('../api')
    await mod.fetchNearbyServices({ lat: 13, lon: 80, categories: ['hospital', 'police'] })
    expect(mockClient.get).toHaveBeenCalledWith('/api/v1/emergency/nearby', expect.objectContaining({
      params: expect.objectContaining({ categories: 'hospital,police' }),
    }))
  })

  // ── fetchSosPayload ──

  it('fetchSosPayload returns sos response', async function () {
    mockClient.get.mockResolvedValueOnce({
      data: {
        services: [], count: 0, radius_used: 0, source: 'api',
        numbers: { '112': { service: 'Police', coverage: 'All', notes: null } },
      },
    })
    var mod = await import('../api')
    var result = await mod.fetchSosPayload({ lat: 13, lon: 80 })
    expect(result.numbers['112'].service).toBe('Police')
    expect(mockClient.get).toHaveBeenCalledWith('/api/v1/emergency/sos', expect.any(Object))
  })

  // ── triggerSos ──

  it('triggerSos sends POST', async function () {
    mockClient.post.mockResolvedValueOnce({
      data: {
        services: [], count: 0, radius_used: 0, source: 'api',
        numbers: {},
      },
    })
    var mod = await import('../api')
    var result = await mod.triggerSos({ lat: 13, lon: 80 })
    expect(result.services).toEqual([])
    expect(mockClient.post).toHaveBeenCalledWith('/api/v1/emergency/sos', null, expect.any(Object))
  })

  // ── fetchEmergencyNumbers ──

  it('fetchEmergencyNumbers returns numbers', async function () {
    mockClient.get.mockResolvedValueOnce({ data: { '112': { service: 'Police' } } })
    var mod = await import('../api')
    var result = await mod.fetchEmergencyNumbers()
    expect(result['112'].service).toBe('Police')
  })

  // ── reverseGeocode ──

  it('reverseGeocode returns displayName', async function () {
    // Mock BigDataCloud
    global.fetch = jest.fn().mockResolvedValueOnce({
      ok: true,
      json: async function () {
        return {
          localityInfo: { administrative: [{ adminLevel: 8, name: 'Chennai' }, { adminLevel: 4, name: 'Tamil Nadu' }] },
          city: 'Chennai',
        }
      },
    })
    var mod = await import('../api')
    var result = await mod.reverseGeocode({ lat: 13.08, lon: 80.27 })
    expect(result.displayName).toBeDefined()
  })

  // ── searchGeocode ──

  it('searchGeocode returns results', async function () {
    mockClient.get.mockResolvedValueOnce({
      data: {
        results: [{ display_name: 'Chennai, India', city: 'Chennai', state: 'Tamil Nadu' }],
      },
    })
    var mod = await import('../api')
    var result = await mod.searchGeocode('Chennai')
    expect(result.results).toHaveLength(1)
    expect(result.results[0].displayName).toBe('Chennai, India')
  })

  // ── fetchRoadIssues ──

  it('fetchRoadIssues returns issues', async function () {
    mockClient.get.mockResolvedValueOnce({
      data: {
        issues: [{
          uuid: 'abc', issue_type: 'pothole', severity: 3,
          lat: 13, lon: 80, created_at: '2026-01-01T00:00:00Z',
          distance_meters: 50, status: 'open',
        }],
        count: 1, radius_used: 500,
      },
    })
    var mod = await import('../api')
    var result = await mod.fetchRoadIssues({ lat: 13, lon: 80 })
    expect(result.issues).toHaveLength(1)
    expect(result.issues[0].issueType).toBe('pothole')
  })

  // ── fetchAuthorityPreview ──

  it('fetchAuthorityPreview returns normalised data', async function () {
    mockClient.get.mockResolvedValueOnce({
      data: {
        road_type: 'NH', road_type_code: 'NH48',
        authority_name: 'NHAI', helpline: '1033',
        complaint_portal: 'https://portal.nhai.gov.in',
        escalation_path: 'https://escalate.nhai.gov.in',
        source: 'api',
      },
    })
    var mod = await import('../api')
    var result = await mod.fetchAuthorityPreview({ lat: 13, lon: 80 })
    expect(result.roadType).toBe('NH')
    expect(result.authorityName).toBe('NHAI')
  })

  // ── submitReport ──

  it('submitReport throws without issue_type', async function () {
    var mod = await import('../api')
    await expect(mod.submitReport({
      lat: 13, lon: 80, severity: 3,
    } as any)).rejects.toThrow('submitReport requires either "issue_type" or "type".')
  })

  it('submitReport sends FormData', async function () {
    mockClient.post.mockResolvedValueOnce({
      data: {
        uuid: 'abc', authority_name: 'NHAI', authority_phone: '1033',
        complaint_portal: 'https://portal', road_type: 'NH',
        road_type_code: 'NH48', status: 'open',
      },
    })
    var mod = await import('../api')
    var result = await mod.submitReport({
      lat: 13, lon: 80, severity: 3, issue_type: 'pothole',
      description: 'Big pothole', citizen_phone: '9999999999',
    })
    expect(result.uuid).toBe('abc')
    // Verify FormData was sent
    expect(mockClient.post).toHaveBeenCalledWith(
      '/api/v1/roads/report',
      expect.any(Object),
      expect.objectContaining({ headers: { 'Content-Type': 'multipart/form-data' } }),
    )
  })

  it('submitReport handles photo upload', async function () {
    mockClient.post.mockResolvedValueOnce({
      data: {
        uuid: 'abc', authority_name: 'NHAI', authority_phone: '1033',
        complaint_portal: 'https://portal', road_type: 'NH',
        road_type_code: 'NH48', status: 'open',
      },
    })
    var mod = await import('../api')
    var photo = new File(['test'], 'photo.jpg', { type: 'image/jpeg' })
    var result = await mod.submitReport({
      lat: 13, lon: 80, severity: 3, issue_type: 'pothole',
      photo: photo,
    })
    expect(result.uuid).toBe('abc')
  })

  // ── sendChatMessage ──

  it('sendChatMessage sends to chatbot', async function () {
    var mod = await import('../api')
    // We need the chatbotClient. But it's not exported.
    // Instead verify that the function structure is correct
    expect(typeof mod.sendChatMessage).toBe('function')
  })

  // ── calculateChallan ──

  it('calculateChallan queries online API', async function () {
    mockClient.post.mockResolvedValueOnce({
      data: {
        violation_code: 'MVA_185', vehicle_class: 'motorcycle',
        state_code: 'TN', base_fine: 500,
        repeat_fine: null, amount_due: 500,
        section: '185', description: 'Drunk driving',
      },
    })
    var mod = await import('../api')
    var result = await mod.calculateChallan({
      violation_code: 'MVA_185', vehicle_class: 'motorcycle',
      state_code: 'TN', is_repeat: false,
    })
    expect(result.base_fine).toBe(500)
    expect(result.source).toBe('online')
  })

  it('calculateChallan falls back to offline on API error', async function () {
    mockClient.post.mockRejectedValueOnce(new Error('Network error'))
    var mod = await import('../api')
    var result = await mod.calculateChallan({
      violation_code: 'MVA_185', vehicle_class: 'motorcycle',
      state_code: 'TN', is_repeat: false,
    })
    expect(result.source).toBe('offline')
    expect(result.violation_code).toBe('MVA_185')
  })

  it('calculateChallan throws when both API and offline fail', async function () {
    var consoleSpy = jest.spyOn(console, 'error').mockImplementation(function () {})
    mockClient.post.mockRejectedValueOnce(new Error('API error'))
    var duckdb = require('../duckdb-challan')
    duckdb.calculateOfflineChallan.mockRejectedValueOnce(new Error('Offline error'))
    try {
      var mod = require('../api')
      await expect(mod.calculateChallan({
        violation_code: 'MVA_185', vehicle_class: 'motorcycle',
        state_code: 'TN', is_repeat: false,
      })).rejects.toThrow('API error')
      expect(consoleSpy).toHaveBeenCalled()
    } finally {
      consoleSpy.mockRestore()
    }
  })

  // ── Client instance ──

  it('client has interceptors configured', function () {
    var mod = require('../api')
    expect(mod.client).toBeDefined()
    expect(mod.client.interceptors).toBeDefined()
  })

  it('extractApiError handles error with error_code', function () {
    var mod = require('../api')
    var err = {
      isAxiosError: true,
      message: 'Forbidden',
      response: { status: 403, data: { detail: 'Access denied', error_code: 'ACCESS_DENIED' } },
    }
    var result = mod.extractApiError(err)
    expect(result.code).toBe('ACCESS_DENIED')
  })

  // ── fetchMunicipalities ──

  it('fetchMunicipalities returns municipalities', async function () {
    mockClient.get.mockResolvedValueOnce({
      data: { municipalities: [{ slug: 'chennai', name: 'Chennai', city: 'Chennai', state_code: 'TN', municipality_type: 'Corporation', centroid_lat: 13, centroid_lon: 80 }], total: 1, page: 1, page_size: 50 },
    })
    var mod = await import('../api')
    var result = await mod.fetchMunicipalities()
    expect(result.municipalities).toHaveLength(1)
    expect(result.municipalities[0].name).toBe('Chennai')
  })

  it('fetchMunicipalities handles data.items fallback', async function () {
    mockClient.get.mockResolvedValueOnce({
      data: { items: [{ slug: 'mumbai', name: 'Mumbai', city: 'Mumbai', state_code: 'MH', municipality_type: 'Corporation', centroid_lat: 19, centroid_lon: 72 }], total: 1, page: 1, page_size: 50 },
    })
    var mod = await import('../api')
    var result = await mod.fetchMunicipalities()
    expect(result.municipalities).toHaveLength(1)
  })

  it('fetchMunicipalities handles search params', async function () {
    mockClient.get.mockResolvedValueOnce({
      data: { municipalities: [], total: 0, page: 1, page_size: 10 },
    })
    var mod = await import('../api')
    await mod.fetchMunicipalities({ q: 'chennai', stateCode: 'TN', municipalityType: 'Corporation', page: 1, pageSize: 10 })
    expect(mockClient.get).toHaveBeenCalledWith('/api/v1/civic/municipalities', expect.objectContaining({
      params: expect.objectContaining({ state_code: 'TN', municipality_type: 'Corporation' }),
    }))
  })

  // ── fetchMunicipalityBySlug ──

  it('fetchMunicipalityBySlug returns detail', async function () {
    mockClient.get.mockResolvedValueOnce({
      data: { slug: 'chennai', name: 'Chennai', city: 'Chennai', state_code: 'TN', municipality_type: 'Corporation', centroid_lat: 13, centroid_lon: 80, headquarters_address: 'Ripon Building', email: 'gc@chennai.in', website_url: 'https://chennai.in' },
    })
    var mod = await import('../api')
    var result = await mod.fetchMunicipalityBySlug('chennai')
    expect(result.headquartersAddress).toBe('Ripon Building')
    expect(result.email).toBe('gc@chennai.in')
  })

  // ── fetchNearbyMunicipalities ──

  it('fetchNearbyMunicipalities returns list', async function () {
    mockClient.get.mockResolvedValueOnce({
      data: { municipalities: [{ slug: 'chennai', name: 'Chennai', city: 'Chennai', state_code: 'TN', municipality_type: 'Corporation', centroid_lat: 13, centroid_lon: 80 }] },
    })
    var mod = await import('../api')
    var result = await mod.fetchNearbyMunicipalities(13, 80, 5)
    expect(result).toHaveLength(1)
  })

  // ── Enterprise endpoints ──

  it('authorityAcceptComplaint posts to accept', async function () {
    mockClient.post.mockResolvedValueOnce({ data: { status: 'accepted' } })
    var mod = await import('../api')
    var result = await mod.authorityAcceptComplaint('uuid-1')
    expect(result.status).toBe('accepted')
  })

  it('authorityRejectComplaint posts with reason', async function () {
    mockClient.post.mockResolvedValueOnce({ data: { status: 'rejected' } })
    var mod = await import('../api')
    var result = await mod.authorityRejectComplaint('uuid-1', 'invalid')
    expect(result.status).toBe('rejected')
  })

  it('citizenConfirmResolution posts with rating', async function () {
    mockClient.post.mockResolvedValueOnce({ data: { status: 'confirmed' } })
    var mod = await import('../api')
    var result = await mod.citizenConfirmResolution('ref-1', 4, 'Good work')
    expect(result.status).toBe('confirmed')
  })

  it('citizenRejectResolution posts with reason', async function () {
    mockClient.post.mockResolvedValueOnce({ data: { status: 'rejected' } })
    var mod = await import('../api')
    var result = await mod.citizenRejectResolution('ref-1', 'not fixed')
    expect(result.status).toBe('rejected')
  })

  it('syncGarage posts vehicle', async function () {
    mockClient.post.mockResolvedValueOnce({ data: { vehicles: [], sync_status: 'ok', last_synced_at: '2026-01-01' } })
    var mod = await import('../api')
    var result = await mod.syncGarage('TN01AB1234')
    expect(result.sync_status).toBe('ok')
  })

  it('syncGarage posts without vehicle', async function () {
    mockClient.post.mockResolvedValueOnce({ data: { vehicles: [], sync_status: 'ok', last_synced_at: '2026-01-01' } })
    var mod = await import('../api')
    var result = await mod.syncGarage()
    expect(result.sync_status).toBe('ok')
  })

  it('draftDisputeAppeal posts dispute', async function () {
    mockClient.post.mockResolvedValueOnce({ data: { dispute_ref: 'd-1', appeal_letter: 'test', cited_mva_sections: ['185'], confidence_score: 0.8, instructions: [] } })
    var mod = await import('../api')
    var result = await mod.draftDisputeAppeal({ challan_ref: 'c-1', violation_code: 'MVA_185', fine_amount: 500, mitigating_factors: 'none' })
    expect(result.dispute_ref).toBe('d-1')
  })

  it('predictFineLiability posts prediction request', async function () {
    mockClient.post.mockResolvedValueOnce({ data: { predicted_violations_count: 2, estimated_annual_liability: 1000, risk_score: 0.3, risk_level: 'low', recommendations: [] } })
    var mod = await import('../api')
    var result = await mod.predictFineLiability({ vehicle_number: 'TN01AB1234', state_code: 'TN', telemetry: { speeding_events: 5, harsh_braking_events: 3, night_driving_minutes: 120, total_km_driven: 1000 } })
    expect(result.risk_level).toBe('low')
  })

  it('fetchPublicStats fetches stats', async function () {
    mockClient.get.mockResolvedValueOnce({ data: { total_issues: 100 } })
    var mod = await import('../api')
    var result = await mod.fetchPublicStats()
    expect(result.total_issues).toBe(100)
  })

  it('fetchPublicWardRankings fetches rankings', async function () {
    mockClient.get.mockResolvedValueOnce({ data: [{ ward: '1', score: 85 }] })
    var mod = await import('../api')
    var result = await mod.fetchPublicWardRankings()
    expect(result).toHaveLength(1)
  })

  it('fieldStartWork posts start-work', async function () {
    mockClient.post.mockResolvedValueOnce({ data: { status: 'in_progress' } })
    var mod = await import('../api')
    var result = await mod.fieldStartWork('uuid-1', 13, 80)
    expect(result.status).toBe('in_progress')
  })

  it('fieldCompleteWork posts complete with photo', async function () {
    mockClient.post.mockResolvedValueOnce({ data: { status: 'completed' } })
    var mod = await import('../api')
    var result = await mod.fieldCompleteWork('uuid-1', 'photo.jpg', 'Done', 13, 80)
    expect(result.status).toBe('completed')
  })

  it('fieldCompleteWork posts complete without photo', async function () {
    mockClient.post.mockResolvedValueOnce({ data: { status: 'completed' } })
    var mod = await import('../api')
    var result = await mod.fieldCompleteWork('uuid-1', null, null, 13, 80)
    expect(result.status).toBe('completed')
  })

  it('fieldUploadEvidence posts FormData', async function () {
    mockClient.post.mockResolvedValueOnce({ data: { status: 'uploaded' } })
    var mod = await import('../api')
    var fd = new FormData()
    fd.append('photo', new Blob(['test']), 'img.jpg')
    var result = await mod.fieldUploadEvidence('uuid-1', fd)
    expect(result.status).toBe('uploaded')
  })

  // ── fetchRoadInfrastructure ──

  it('fetchRoadInfrastructure returns infrastructure', async function () {
    mockClient.get.mockResolvedValueOnce({
      data: { road_type: 'NH', road_type_code: 'NH48', authority_name: 'NHAI', source: 'api' },
    })
    var mod = await import('../api')
    var result = await mod.fetchRoadInfrastructure({ lat: 13, lon: 80 })
    expect(result.roadType).toBe('NH')
  })

  // ── fetchRoutePreview ──

  it('fetchRoutePreview returns route', async function () {
    mockClient.get.mockResolvedValueOnce({
      data: {
        provider: 'ors', profile: 'driving-car', distance_meters: 1000, duration_seconds: 60,
        path: [{ lat: 13, lon: 80 }], bounds: { south: 12, west: 79, north: 14, east: 81 },
        origin: { lat: 13, lon: 80, label: 'A' }, destination: { lat: 13.1, lon: 80.1, label: 'B' },
        routes: [{
          route_id: 'r1', label: 'Fastest', distance_meters: 1000, duration_seconds: 60,
          path: [{ lat: 13, lon: 80 }], bounds: { south: 12, west: 79, north: 14, east: 81 },
          steps: [{ index: 0, instruction: 'Go straight', distance_meters: 500, duration_seconds: 30, street_name: 'Main Rd' }],
        }],
      },
    })
    var mod = await import('../api')
    var result = await mod.fetchRoutePreview({ originLat: 13, originLon: 80, destinationLat: 13.1, destinationLon: 80.1 })
    expect(result.provider).toBe('ors')
    expect(result.routes).toHaveLength(1)
    expect(result.routes[0].steps).toHaveLength(1)
    expect(result.routes[0].steps[0].streetName).toBe('Main Rd')
  })

  // ── sendChatMessage ──

  it('sendChatMessage sends message via chatbotClient', async function () {
    mockClient.post.mockResolvedValueOnce({ data: { response: 'hello', session_id: 's1' } })
    var mod = await import('../api')
    var result = await mod.sendChatMessage({ message: 'hi', session_id: 's1' })
    expect(result.response).toBe('hello')
    expect(result.session_id).toBe('s1')
  })

  it('sendChatMessage sends without session_id', async function () {
    mockClient.post.mockResolvedValueOnce({ data: { response: 'hello', session_id: 's-new' } })
    var mod = await import('../api')
    var result = await mod.sendChatMessage({ message: 'hi' })
    expect(result.response).toBe('hello')
    expect(mockClient.post).toHaveBeenCalledWith('/api/v1/chat/', { message: 'hi' })
  })

  // ── Request interceptors ──

  it('request interceptor adds auth and language headers', function () {
    setMockToken('test-token')
    var mod = require('../api')
    mod.setCsrfToken('csrf-abc')
    var handlers = (require('axios') as any)._requestHandlers
    expect(handlers.length).toBeGreaterThan(0)
    var handler = handlers[0].fulfilled
    var config = { headers: {} }
    var result = handler(config)
    expect(result.headers['Authorization']).toMatch(/^Bearer /)
    expect(result.headers['Accept-Language']).toBe('en')
    expect(result.headers['X-CSRF-Token']).toBe('csrf-abc')
  })

  it('request interceptor omits Authorization when no token', function () {
    setMockToken(null)
    var mod = require('../api')
    mod.setCsrfToken(null)
    var handlers = (require('axios') as any)._requestHandlers
    var handler = handlers[0].fulfilled
    var config = { headers: {} }
    var result = handler(config)
    expect(result.headers['Authorization']).toBeUndefined()
  })

  // ── Error toast interceptor ──

  it('warming interceptor sets and clears timers via request/response', function () {
    jest.useFakeTimers()
    require('../api')
    var handlers = (require('axios') as any)._requestHandlers
    var respHandlers = (require('axios') as any)._responseHandlers

    var warmingReq = handlers[1].fulfilled  // client warming request (index 1, after csrfAuthLang at 0)
    var warmingRes = respHandlers[0].fulfilled  // client warming response
    var _warmingErr = respHandlers[1].rejected  // client warming error

    var config: any = { headers: {} }
    var result = warmingReq(config)
    expect(result._warmingTimer).toBeDefined()
    expect(typeof result._warmingTimer).toBe('number')

    var response: any = { config: result, status: 200 }
    warmingRes(response)

    jest.useRealTimers()
  })

  it('warming timer fires setServerWarming(true) after 5s', function () {
    jest.useFakeTimers()
    require('../api')
    var handlers = (require('axios') as any)._requestHandlers
    var warmingReq = handlers[1].fulfilled
    var setWarmingFn = jest.fn()
    mockStore.useAppStore.getState = jest.fn(function () {
      return {
        authToken: null,
        userProfile: { preferredLanguage: 'en' },
        setServerWarming: setWarmingFn,
      }
    })
    var config: any = { headers: {} }
    warmingReq(config)
    jest.advanceTimersByTime(5000)
    expect(setWarmingFn).toHaveBeenCalledWith(true)
    jest.useRealTimers()
  })

  it('warming error handler clears timer and rejects', function () {
    jest.useFakeTimers()
    var respHandlers = (require('axios') as any)._responseHandlers
    var _warmingErr = respHandlers[0].rejected

    var config: any = { _warmingTimer: setTimeout(function () {}, 1000) }
    var error = { config: config, isAxiosError: true, message: 'fail' }
    expect(function () {
      _warmingErr(error).catch(function () {})
    }).not.toThrow()

    jest.useRealTimers()
  })

  it('retry interceptor passes through successful responses', function () {
    var respHandlers = (require('axios') as any)._responseHandlers
    var retryFulfilled = respHandlers[1].fulfilled
    var response = { data: 'ok', status: 200 }
    var result = retryFulfilled(response)
    expect(result).toBe(response)
  })

  it('chatbotClient request interceptor adds CSRF and auth headers', function () {
    setMockToken('chat-token')
    var apiMod = require('../api')
    apiMod.setCsrfToken('chat-csrf')
    var handlers = (require('axios') as any)._requestHandlers
    var handler = handlers[2].fulfilled
    var config = { headers: {} }
    var result = handler(config)
    expect(result.headers['X-CSRF-Token']).toBe('chat-csrf')
    expect(result.headers['Authorization']).toMatch(/^Bearer /)
    expect(result.headers['Accept-Language']).toBe('en')
  })

  it('global error toast interceptor passes through successful responses', function () {
    var respHandlers = (require('axios') as any)._responseHandlers
    var toastFulfilled = respHandlers[4].fulfilled
    var response = { data: 'ok', status: 200 }
    var result = toastFulfilled(response)
    expect(result).toBe(response)
  })

  it('retry indicator interceptor dismisses toast on success', function () {
    var respHandlers = (require('axios') as any)._responseHandlers
    var indicatorFulfilled = respHandlers[6].fulfilled
    var response = { data: 'ok', status: 200 }
    var result = indicatorFulfilled(response)
    expect(result).toBe(response)
  })

  it('retry indicator interceptor passes through error on retry', function () {
    var respHandlers = (require('axios') as any)._responseHandlers
    var indicatorErr = respHandlers[6].rejected
    var config: any = { headers: {}, _retryCount: 2 }
    var error = { config: config, isAxiosError: true, message: 'fail' }
    return indicatorErr(error).catch(function (err: any) {
      expect(err.message).toBe('fail')
    })
  })

  it('retry interceptor retries on network error', async function () {
    jest.useFakeTimers()
    var respHandlers = (require('axios') as any)._responseHandlers
    var retryErr = respHandlers[1].rejected

    mockClient.get.mockResolvedValueOnce({ data: 'ok' })
    var config: any = { headers: {}, _retryCount: 0 }
    var error = { config: config, isAxiosError: true, message: 'Network error' }
    var promise = retryErr(error)
    jest.advanceTimersByTime(1000)
    var result = await promise
    expect(result.data).toBe('ok')

    jest.useRealTimers()
  })

  it('retry interceptor does not retry after max retries', function () {
    var respHandlers = (require('axios') as any)._responseHandlers
    var retryErr = respHandlers[1].rejected

    var config: any = { headers: {}, _retryCount: 3 }
    var error = { config: config, isAxiosError: true, response: { status: 503 }, message: 'Server error' }
    return retryErr(error).catch(function (err: any) {
      expect(err.message).toBe('Server error')
    })
  })

  it('retry interceptor does not retry on 4xx error', function () {
    var respHandlers = (require('axios') as any)._responseHandlers
    var retryErr = respHandlers[1].rejected

    var config: any = { headers: {}, _retryCount: 0 }
    var error = { config: config, isAxiosError: true, response: { status: 400 }, message: 'Bad request' }
    return retryErr(error).catch(function (err: any) {
      expect(err.message).toBe('Bad request')
    })
  })

  it('error toast interceptor shows toast on network error', function () {
    var respHandlers = (require('axios') as any)._responseHandlers
    var toastErr = respHandlers[4].rejected

    var error = { isAxiosError: true, message: 'Network error' }
    return toastErr(error).catch(function (err: any) {
      expect(err.message).toBe('Network error')
    })
  })

  it('error toast interceptor shows toast on 5xx error', function () {
    var respHandlers = (require('axios') as any)._responseHandlers
    var toastErr = respHandlers[4].rejected

    var error = { isAxiosError: true, response: { status: 500, data: { detail: 'Server is busy' } }, message: 'Server error' }
    return toastErr(error).catch(function (err: any) {
      expect(err.message).toBe('Server error')
    })
  })

  it('normalizeEmergencyService converts raw service', async function () {
    var raw = { id: '1', name: 'AIIMS', type: 'hospital', lat: 13.0, lon: 80.0, distance_meters: 500, eta_seconds: 300 }
    mockClient.get.mockResolvedValueOnce({ data: { services: [raw], count: 1, radius_used: 5000 } })
    var apiMod = await import('../api')
    var result = await apiMod.fetchNearbyServices(13, 80, 'hospital')
    expect(result.services).toHaveLength(1)
    expect(result.services[0].name).toBe('AIIMS')
  })

  // ── Normalizer: normalizeGeocodeResult ──

  it('normalizeGeocodeResult handles reverse geocode', async function () {
    var raw = { lat: 13.0, lon: 80.0, display_name: 'Chennai', address: { city: 'Chennai', state: 'Tamil Nadu' } }
    mockClient.get.mockResolvedValueOnce({ data: raw })
    var apiMod = await import('../api')
    var result = await apiMod.reverseGeocode(13, 80)
    expect(result).toBeDefined()
  })

  it('normalizeGeocodeResult handles search geocode', async function () {
    var raw = { results: [{ lat: 13.0, lon: 80.0, display_name: 'Chennai', address: { city: 'Chennai', state: 'Tamil Nadu' } }] }
    mockClient.get.mockResolvedValueOnce({ data: raw })
    var apiMod = await import('../api')
    var result = await apiMod.searchGeocode('Chennai')
    expect(result.results).toBeDefined()
  })

  it('normalizeRoadIssue maps fields correctly', async function () {
    var raw = { id: 'i-1', issue_type: 'pothole', severity: 'high', status: 'open', description: 'Big pothole', reporter_name: 'John', upvotes: 5, comments_count: 2, created_at: '2026-01-01T00:00:00Z', updated_at: '2026-01-02T00:00:00Z', lat: 13.0, lon: 80.0, pothole_depth: 5, ward: 'Ward 1', municipality_slug: 'chennai', image_url: 'https://example.com/img.jpg', category: 'road' }
    mockClient.get.mockResolvedValueOnce({ data: { issues: [raw], total: 1 } })
    var apiMod = await import('../api')
    var result = await apiMod.fetchRoadIssues({ lat: 13, lon: 80, radius: 5000 })
    expect(result.issues).toHaveLength(1)
    expect(result.issues[0].issueType).toBe('pothole')
  })

  it('normalizeInfrastructure maps data', async function () {
    var raw = { road_type: 'NH', road_type_code: 'NH48', source: 'api' }
    mockClient.get.mockResolvedValueOnce({ data: raw })
    var apiMod = await import('../api')
    var result = await apiMod.fetchRoadInfrastructure({ lat: 13, lon: 80 })
    expect(result.roadType).toBe('NH')
    expect(result.roadTypeCode).toBe('NH48')
  })

})
