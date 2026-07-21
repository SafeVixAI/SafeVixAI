// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
jest.mock('idb', function () { return { openDB: jest.fn() } })
jest.mock('../supabase-auth', function () { return { getSupabaseBrowserClient: jest.fn() } })

var mockDb = { put: jest.fn(), getAllFromIndex: jest.fn(), createObjectStore: jest.fn(function() { return { createIndex: jest.fn() } }), objectStoreNames: { contains: jest.fn(function() { return false }) } }
var mockOpenDB = require('idb').openDB
mockOpenDB.mockImplementation(function(name, version, opts) {
  if (opts && opts.upgrade) opts.upgrade(mockDb)
  return Promise.resolve(mockDb)
})

function makeFromMock(data?: any, error?: any) {
  return jest.fn(function () { return { select: jest.fn(function () { return { eq: jest.fn(function () { return { order: jest.fn(function () { return { data: data ?? null, error: error ?? null } }) } }) } }), insert: jest.fn(function () { return {} }) } })
}

var mockSupabase = {
  from: makeFromMock(),
}
var mockSupabaseAuth = require('../supabase-auth')
mockSupabaseAuth.getSupabaseBrowserClient.mockReturnValue(mockSupabase)

if (typeof window !== 'undefined') {
  Object.defineProperty(window, 'indexedDB', { value: {}, writable: true, configurable: true })
}

var _ChatLog
beforeEach(function() {
  mockSupabase.from = makeFromMock()
  mockSupabaseAuth.getSupabaseBrowserClient.mockClear()
  mockSupabaseAuth.getSupabaseBrowserClient.mockReturnValue(mockSupabase)
  mockOpenDB.mockClear()
  mockOpenDB.mockImplementation(function(name, version, opts) {
    if (opts && opts.upgrade) opts.upgrade(mockDb)
    return Promise.resolve(mockDb)
  })
  mockDb.put.mockClear()
  mockDb.getAllFromIndex.mockClear()
})
beforeAll(async function () {
  var mod = await import('../chat-history')
  _ChatLog = mod.ChatLog
})

describe('chat-history', function () {
  describe('loadChatHistory', function () {
    it('returns empty array when db not available', async function () {
      mockOpenDB.mockResolvedValueOnce(null)
      var result = await (await import('../chat-history')).loadChatHistory('session-1')
      expect(result).toEqual([])
    })

    it('maps supabase data to ChatLog when data returned', async function () {
      mockSupabase.from = makeFromMock([{ message_id: 'm1', role: 'assistant', content: 'Hello', metadata: { timestamp: '12:00', citations: ['law1'], provider: 'groq' }, created_at: '2024-01-01' }], null)
      var result = await (await import('../chat-history')).loadChatHistory('session-1')
      expect(result).toHaveLength(1)
      expect(result[0].id).toBe('m1')
      expect(result[0].role).toBe('ai')
      expect(result[0].text).toBe('Hello')
      expect(result[0].citations).toEqual(['law1'])
      expect(result[0].provider).toBe('groq')
    })

    it('falls back to indexedDB when supabase errors', async function () {
      mockSupabase.from = makeFromMock(null, new Error('fail'))
      mockDb.getAllFromIndex.mockResolvedValueOnce([{ id: 'i1', sessionId: 'session-1', role: 'user', text: 'fallback', timestamp: 'now', citations: [], createdAt: '2024-01-01' }])
      var result = await (await import('../chat-history')).loadChatHistory('session-1')
      expect(result).toHaveLength(1)
      expect(result[0].id).toBe('i1')
      expect(result[0].text).toBe('fallback')
      expect(mockDb.getAllFromIndex).toHaveBeenCalledWith('chat-logs', 'sessionId', 'session-1')
    })
  })

  describe('appendChatLog', function () {
    it('handles db put call', async function () {
      var log = { id: '1', sessionId: 's1', role: 'user', text: 'hi', timestamp: 'now', createdAt: 'now' }
      await (await import('../chat-history')).appendChatLog(log)
      expect(mockDb.put).toHaveBeenCalled()
    })

    it('skips db put when openChatDb returns null', async function () {
      mockOpenDB.mockResolvedValueOnce(null)
      mockDb.put.mockClear()
      var log = { id: '2', sessionId: 's1', role: 'user', text: 'no db', timestamp: 'now', createdAt: 'now' }
      await (await import('../chat-history')).appendChatLog(log)
      expect(mockDb.put).not.toHaveBeenCalled()
    })

    it('skips supabase insert when getSupabaseBrowserClient returns null', async function () {
      mockSupabaseAuth.getSupabaseBrowserClient.mockReturnValueOnce(null)
      var log = { id: '3', sessionId: 's1', role: 'user', text: 'no supabase', timestamp: 'now', createdAt: 'now' }
      await (await import('../chat-history')).appendChatLog(log)
      expect(mockSupabase.from).not.toHaveBeenCalled()
    })

    it('skips supabase insert when offline', async function () {
      var origOnLine = navigator.onLine
      Object.defineProperty(navigator, 'onLine', { value: false, configurable: true, writable: true })
      var log = { id: '4', sessionId: 's1', role: 'user', text: 'offline', timestamp: 'now', createdAt: 'now' }
      await (await import('../chat-history')).appendChatLog(log)
      expect(mockSupabase.from).not.toHaveBeenCalled()
      Object.defineProperty(navigator, 'onLine', { value: origOnLine, configurable: true, writable: true })
    })
  })

  describe('loadChatHistory', function () {
    it('returns empty array when supabase errors and indexedDB is null', async function () {
      mockSupabase.from = makeFromMock(null, new Error('fail'))
      mockOpenDB.mockResolvedValueOnce(null)
      var result = await (await import('../chat-history')).loadChatHistory('session-1')
      expect(result).toEqual([])
    })
  })
})
