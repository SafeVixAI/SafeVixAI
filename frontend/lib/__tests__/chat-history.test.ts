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

var mockSupabase = {
  from: jest.fn(function () { return { select: jest.fn(function () { return { eq: jest.fn(function () { return { order: jest.fn(function () { return { data: null, error: null } }) } }) } }), insert: jest.fn(function () { return {} }) } })
}
var mockSupabaseAuth = require('../supabase-auth')
mockSupabaseAuth.getSupabaseBrowserClient.mockReturnValue(mockSupabase)

if (typeof window !== 'undefined') {
  Object.defineProperty(window, 'indexedDB', { value: {}, writable: true, configurable: true })
}

var defaultFrom = jest.fn(function () { return { select: jest.fn(function () { return { eq: jest.fn(function () { return { order: jest.fn(function () { return { data: null, error: null } }) } }) } }), insert: jest.fn(function () { return {} }) } })
var ChatLog
beforeEach(function() { mockSupabase.from = defaultFrom })
beforeAll(async function () {
  var mod = await import('../chat-history')
  ChatLog = mod.ChatLog
})

describe('chat-history', function () {
  describe('loadChatHistory', function () {
    it('returns empty array when db not available', async function () {
      mockOpenDB.mockResolvedValueOnce(null)
      var result = await (await import('../chat-history')).loadChatHistory('session-1')
      expect(result).toEqual([])
    })

    it('maps supabase data to ChatLog when data returned', async function () {
      mockSupabase.from = jest.fn(function () { return { select: jest.fn(function () { return { eq: jest.fn(function () { return { order: jest.fn(function () { return { data: [{ message_id: 'm1', role: 'assistant', content: 'Hello', metadata: { timestamp: '12:00', citations: ['law1'], provider: 'groq' }, created_at: '2024-01-01' }], error: null } }) } }) } }), insert: jest.fn(function () { return {} }) } })
      var result = await (await import('../chat-history')).loadChatHistory('session-1')
      expect(result).toHaveLength(1)
      expect(result[0].id).toBe('m1')
      expect(result[0].role).toBe('ai')
      expect(result[0].text).toBe('Hello')
      expect(result[0].citations).toEqual(['law1'])
      expect(result[0].provider).toBe('groq')
    })

    it('falls back to indexedDB when supabase errors', async function () {
      mockSupabase.from = jest.fn(function () { return { select: jest.fn(function () { return { eq: jest.fn(function () { return { order: jest.fn(function () { return { data: null, error: new Error('fail') } }) } }) } }), insert: jest.fn(function () { return {} }) } })
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
  })
})
