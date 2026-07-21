'use client';

// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
import React from 'react';


import { useState, useRef, useEffect, useCallback } from 'react';
import { useAppStore } from '@/lib/store';
import { useGeolocation } from '@/lib/geolocation';
import { ConnectivityBadge } from './ConnectivityBadge';
import { Send, Wifi, WifiOff, Loader2, Bot, UserCircle } from 'lucide-react';
import { getOfflineAI, askOfflineAI } from '@/lib/offline-ai';
import { logClientError } from '@/lib/client-logger';
import { PUBLIC_CHATBOT_BASE_URL } from '@/lib/public-env';
import { useShallow } from 'zustand/react/shallow';

// ── Types ──────────────────────────────────────────────────────────────────
interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  sources?: string[];
  streaming?: boolean;
}

const CHATBOT_URL = PUBLIC_CHATBOT_BASE_URL;

// ── Helper: call backend SSE stream ───────────────────────────────────────
async function* streamChat(
  message: string,
  session_id: string,
  lat?: number,
  lon?: number,
): AsyncGenerator<{ type: string; text?: string; intent?: string; sources?: string[]; session_id?: string; message?: string }> {
  // H5 FIX: Include auth token in chat streaming request
  const authToken = useAppStore.getState().authToken;
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (authToken) headers['Authorization'] = `Bearer ${authToken}`;

  const resp = await fetch(`${CHATBOT_URL}/api/v1/chat/stream`, {
    method: 'POST',
    headers,
    body: JSON.stringify({ message, session_id, lat, lon }),
  });

  if (!resp.ok || !resp.body) {
    throw new Error(`Chat error: ${resp.status}`);
  }

  const reader = resp.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop() ?? '';
    for (const line of lines) {
      if (line.startsWith('data: ')) {
        try {
          yield JSON.parse(line.slice(6));
        } catch {
          // malformed — skip
        }
      }
    }
  }
}

// ── Component ──────────────────────────────────────────────────────────────
export function ChatInterface() {
  const { aiMode, setAiMode } = useAppStore(useShallow((s) => ({ aiMode: s.aiMode, setAiMode: s.setAiMode })));
  const { location } = useGeolocation();

  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'greeting',
      role: 'assistant',
      content:
        'Hello! I am your SafeVixAI assistant. Ask me about traffic rules, emergency procedures, first aid, challan fines, or pothole reporting.',
    },
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId] = useState(() => typeof crypto !== 'undefined' && crypto.randomUUID ? `session-${crypto.randomUUID()}` : `session-${Date.now()}`);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // ── Send message ─────────────────────────────────────────────────────────
  const handleSubmit = useCallback(
    async (e?: React.FormEvent, overrideText?: string) => {
      e?.preventDefault();
      const text = overrideText ?? input.trim();
      if (!text || isLoading) return;

      const userMsg: Message = { id: Date.now().toString(), role: 'user', content: text };
      setMessages((prev) => [...prev, userMsg]);
      setInput('');
      setIsLoading(true);

      // Placeholder for streaming response
      const assistantId = `assistant-${Date.now()}`;
      setMessages((prev) => [
        ...prev,
        { id: assistantId, role: 'assistant', content: '', streaming: true },
      ]);

      try {
        if (aiMode === 'online' || aiMode === 'loading') {
          // ── SSE streaming from backend ──────────────────────────────────
          let accumulated = '';
          let finalSources: string[] = [];

          for await (const event of streamChat(text, sessionId, location?.lat, location?.lon)) {
            if (event.type === 'token' && event.text) {
              accumulated += event.text;
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === assistantId ? { ...m, content: accumulated } : m,
                ),
              );
            } else if (event.type === 'done') {
              finalSources = event.sources ?? [];
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === assistantId
                    ? { ...m, content: accumulated, sources: finalSources, streaming: false }
                    : m,
                ),
              );
            } else if (event.type === 'error') {
              throw new Error(event.message ?? 'Stream error');
            }
          }
        } else {
          // ── Offline AI ────────────────────────────────────────────────
          // Ensure offline AI is initialized
          await getOfflineAI();
          const offlineReply = await askOfflineAI(text);
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId
                ? { ...m, content: offlineReply, streaming: false }
                : m,
            ),
          );
        }
      } catch (err) {
        logClientError('Chat error:', err);
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantId
              ? {
                  ...m,
                  content:
                    'Sorry, I encountered an error. Please check your connection or switch to Offline Mode.',
                  streaming: false,
                }
              : m,
          ),
        );
      } finally {
        setIsLoading(false);
      }
    },
    [aiMode, input, isLoading, sessionId, location],
  );

  // ── Keyboard shortcut ────────────────────────────────────────────────────
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  // ── Render ───────────────────────────────────────────────────────────────
  return (
    <div className="flex flex-col h-full bg-surface-2 dark:bg-bg">
      {/* HEADER / MODE TOGGLE */}
      <div className="flex justify-between items-center px-4 py-3 border-b border-border-md dark:border-white/5 bg-white/80 dark:bg-white/5 backdrop-blur-xl">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-xl bg-brand/10 flex items-center justify-center">
            <Bot size={16} className="text-brand" />
          </div>
          <span className="text-sm font-semibold text-text-1 dark:text-white uppercase tracking-tight">
            SafeVixAI Chat
          </span>
          <ConnectivityBadge />
        </div>

        {/* Mode toggle */}
        <div className="flex items-center bg-surface-2 dark:bg-white/5 rounded-full p-0.5 border border-border-md dark:border-white/10">
          <button
            onClick={() => setAiMode('online')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-[10px] font-semibold uppercase tracking-widest transition-all ${
              aiMode === 'online'
                ? 'bg-brand text-brand-foreground shadow-sm'
                : 'text-text-2 hover:text-text-1 dark:hover:text-text-3'
            }`}
          >
            <Wifi size={12} />
            Online
          </button>
          <button
            onClick={() => setAiMode('offline')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-[10px] font-semibold uppercase tracking-widest transition-all ${
              aiMode === 'offline'
                ? 'bg-brand text-brand-foreground shadow-sm'
                : 'text-text-2 hover:text-text-1 dark:hover:text-text-3'
            }`}
          >
            <WifiOff size={12} />
            Offline
          </button>
        </div>
      </div>

      {/* CHAT MESSAGES */}
      <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-4 scrollbar-hide" role="log" aria-live="polite" aria-label="Chat messages">
        {messages.map((msg) => {
          const isUser = msg.role === 'user';
          return (
            <div
              key={msg.id}
              className={`flex flex-col ${isUser ? 'items-end' : 'items-start'} animate-fade-in-up`}
            >
              <div
                className={`flex items-start gap-2.5 ${isUser ? 'flex-row-reverse' : 'flex-row'} max-w-[85%]`}
              >
                <div
                  className={`w-7 h-7 rounded-xl flex items-center justify-center flex-shrink-0 mt-1 ${
                    isUser ? 'bg-brand text-brand-foreground' : 'bg-brand/10 text-brand-light'
                  }`}
                >
                  {isUser ? <UserCircle size={14} /> : <Bot size={14} />}
                </div>

                <div
                  className={`px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap ${
                    isUser
                      ? 'bg-brand/20 text-text-1 rounded-lg rounded-tr-sm border border-brand/30 shadow-md'
                      : 'bg-surface-2 text-text-1 rounded-lg rounded-tl-sm border border-border shadow-sm'
                  }`}
                >
                  {msg.content || (msg.streaming ? '' : '…')}
                  {/* Streaming cursor */}
                  {msg.streaming && (
                    <span className="inline-block w-0.5 h-4 bg-current ml-0.5 animate-pulse" />
                  )}
                </div>
              </div>

              {/* Sources */}
              {msg.sources && msg.sources.length > 0 && (
                <div className="mt-1 ml-9 flex flex-wrap gap-1.5">
                  {msg.sources.map((src) => (
                    <span
                      key={src}
                      className="text-[10px] px-2 py-0.5 rounded-full bg-surface-2 dark:bg-white/5 text-text-2 dark:text-text-2 border border-border-md dark:border-white/10"
                    >
                      {src}
                    </span>
                  ))}
                </div>
              )}
            </div>
          );
        })}

        {/* Loading dots (shown before first streaming token arrives) */}
        {isLoading && !messages.some((m) => m.streaming) && (
          <div className="flex items-start gap-2.5 self-start">
            <div className="w-7 h-7 rounded-xl bg-brand-light/10 flex items-center justify-center">
              <Bot size={14} className="text-brand-light" />
            </div>
            <div className="px-4 py-3 bg-white dark:bg-white/5 rounded-lg rounded-tl-sm border border-border-md dark:border-white/10 flex gap-1.5">
              <span className="w-2 h-2 rounded-full bg-text-3 dark:bg-text-3 animate-bounce" style={{ animationDelay: '0ms' }} />
              <span className="w-2 h-2 rounded-full bg-text-3 dark:bg-text-3 animate-bounce" style={{ animationDelay: '150ms' }} />
              <span className="w-2 h-2 rounded-full bg-text-3 dark:bg-text-3 animate-bounce" style={{ animationDelay: '300ms' }} />
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* INPUT */}
      <div className="px-4 py-3 bg-white/80 dark:bg-white/5 backdrop-blur-xl border-t border-border-md dark:border-white/5">
        <form onSubmit={handleSubmit} className="flex items-center gap-3">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={
              aiMode === 'offline'
                ? 'Ask a question (offline mode)…'
                : 'Ask about traffic rules, first aid, emergencies…'
            }
            disabled={isLoading}
            aria-label="Chat message input"
            className="flex-1 px-4 py-3 rounded-lg bg-surface-1 border border-border text-sm text-text-1 placeholder:text-text-3 focus:outline-none focus:ring-2 focus:ring-brand/30 focus:border-brand/50 transition-all"
          />
          <button
            type="submit"
            disabled={!input.trim() || isLoading}
            aria-label="Send message"
            className={`w-11 h-11 rounded-full flex items-center justify-center flex-shrink-0 transition-all active:scale-90 ${
              !input.trim() || isLoading
                ? 'bg-surface-3 text-text-3 cursor-not-allowed'
                : 'bg-brand text-brand-foreground shadow-md hover:bg-brand/90'
            }`}
          >
            {isLoading ? <Loader2 size={16} className="animate-spin" /> : <Send size={16} />}
          </button>
        </form>
      </div>
    </div>
  );
}