// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

import { openDB } from 'idb';
import { getSupabaseBrowserClient } from './supabase-auth';

export interface ChatLog {
  id: string;
  sessionId: string;
  role: 'user' | 'ai' | 'system';
  text: string;
  timestamp: string;
  citations?: string[];
  provider?: string;
  createdAt: string;
}

const DB_NAME = 'safevix-chat-db';
const STORE_NAME = 'chat-logs';

const isBrowser = () => /* istanbul ignore next */
typeof window !== 'undefined' && 'indexedDB' in window;

async function openChatDb() {
  if (!isBrowser()) return null;
  return openDB(DB_NAME, 1, {
    upgrade(db) {
      if (!db.objectStoreNames.contains(STORE_NAME)) {
        const store = db.createObjectStore(STORE_NAME, { keyPath: 'id' });
        store.createIndex('sessionId', 'sessionId');
      }
    },
  });
}

interface SupabaseChatRow {
  message_id: string | null;
  role: string;
  content: string | null;
  metadata: {
    id?: string;
    timestamp?: string;
    citations?: string[];
    provider?: string;
  } | null;
  created_at: string;
}

export async function loadChatHistory(sessionId: string): Promise<ChatLog[]> {
  const supabase = getSupabaseBrowserClient();
  if (supabase) {
    const { data, error } = await supabase
      .from('chat_logs')
      .select('message_id, role, content, metadata, created_at')
      .eq('session_id', sessionId)
      .order('created_at', { ascending: true });

    if (!error && data) {
      return (data as unknown as SupabaseChatRow[]).map((row: SupabaseChatRow) => ({
        id: row.message_id || row.metadata?.id || row.created_at,
        sessionId,
        role: row.role === 'assistant' ? 'ai' : row.role as 'user' | 'ai' | 'system',
        text: row.content || '',
        timestamp: row.metadata?.timestamp || '',
        citations: row.metadata?.citations || [],
        provider: row.metadata?.provider,
        createdAt: row.created_at,
      }));
    }
  }

  const db = await openChatDb();
  if (!db) return [];
  const logs = await db.getAllFromIndex(STORE_NAME, 'sessionId', sessionId);
  return logs.sort((a, b) => a.createdAt.localeCompare(b.createdAt));
}

export async function appendChatLog(log: ChatLog) {
  const db = await openChatDb();
  if (db) {
    await db.put(STORE_NAME, log);
  }

  const supabase = getSupabaseBrowserClient();
  if (!supabase || (typeof navigator !== 'undefined' && !navigator.onLine)) return;

  await supabase.from('chat_logs').insert({
    session_id: log.sessionId,
    message_id: log.id,
    role: log.role === 'ai' ? 'assistant' : log.role,
    content: log.text,
    metadata: {
      timestamp: log.timestamp,
      citations: log.citations || [],
      provider: log.provider,
    },
    created_at: log.createdAt,
  });
}
