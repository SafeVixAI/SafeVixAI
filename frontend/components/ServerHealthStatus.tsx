// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
import React from 'react';

'use client';

import { useState, useEffect } from 'react';
import { PUBLIC_API_BASE_URL, PUBLIC_CHATBOT_BASE_URL } from '@/lib/public-env';

type ServiceStatus = 'checking' | 'online' | 'offline';

interface HealthResult {
  backend: ServiceStatus;
  chatbot: ServiceStatus;
  db: ServiceStatus;
}

export function ServerHealthStatus() {
  const [health, setHealth] = useState<HealthResult>({
    backend: 'checking',
    chatbot: 'checking',
    db: 'checking',
  });
  const [expanded, setExpanded] = useState(false);

  useEffect(() => {
    if (typeof fetch === 'undefined') return;
    let terminated = false;

    const check = async () => {
      const [backendRes, chatbotRes] = await Promise.allSettled([
        fetch(`${PUBLIC_API_BASE_URL}/health`, { cache: 'no-store' }),
        fetch(`${PUBLIC_CHATBOT_BASE_URL}/health`, { cache: 'no-store' }),
      ]);

      if (terminated) return;

      let db: ServiceStatus = 'offline';
      if (backendRes.status === 'fulfilled' && backendRes.value.ok) {
        try {
          const data = await backendRes.value.json();
          db = data.database_available ? 'online' : 'offline';
        } catch { db = 'offline'; }
      }

      setHealth({
        backend: backendRes.status === 'fulfilled' && backendRes.value.ok ? 'online' : 'offline',
        chatbot: chatbotRes.status === 'fulfilled' && chatbotRes.value.ok ? 'online' : 'offline',
        db,
      });
    };

    check();
    const interval = setInterval(check, 60_000);
    return () => { terminated = true; clearInterval(interval); };
  }, []);

  const dot = (status: ServiceStatus) => {
    if (status === 'checking') return <span className="size-1.5 rounded-full bg-yellow-400 animate-pulse" />;
    if (status === 'online') return <span className="size-1.5 rounded-full bg-green-400" />;
    return <span className="size-1.5 rounded-full bg-red-400" />;
  };

  return (
    <div className="fixed bottom-20 right-3 lg:bottom-4 lg:right-4 z-[998]">
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex items-center gap-1.5 px-2 py-1 rounded-lg border border-[var(--border-md)] bg-[var(--surface-2)]/80 backdrop-blur-sm text-[10px] font-mono text-[var(--text-3)] hover:text-[var(--text-1)] hover:border-[var(--border-lg)] transition-all shadow-lg"
        title="Server health status"
        aria-label={expanded ? 'Collapse server status' : 'Expand server status'}
      >
        <span className="flex items-center gap-1">
          {dot(health.backend)}
          <span>API</span>
        </span>
        <span className="flex items-center gap-1">
          {dot(health.chatbot)}
          <span>AI</span>
        </span>
      </button>
      {expanded && (
        <div className="absolute bottom-full right-0 mb-2 w-44 rounded-lg border border-[var(--border-md)] bg-[var(--surface-3)] p-3 text-[11px] shadow-xl backdrop-blur-md z-50">
          <div className="flex flex-col gap-2">
            <div className="flex items-center justify-between">
              <span className="text-[var(--text-3)]">Backend</span>
              <span className="flex items-center gap-1.5">
                {dot(health.backend)}
                <span className={health.backend === 'online' ? 'text-green-400' : 'text-red-400'}>
                  {health.backend === 'online' ? 'Online' : health.backend === 'checking' ? '...' : 'Offline'}
                </span>
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-[var(--text-3)]">Database</span>
              <span className="flex items-center gap-1.5">
                {dot(health.db)}
                <span className={health.db === 'online' ? 'text-green-400' : 'text-red-400'}>
                  {health.db === 'online' ? 'Online' : health.db === 'checking' ? '...' : 'Offline'}
                </span>
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-[var(--text-3)]">Chatbot AI</span>
              <span className="flex items-center gap-1.5">
                {dot(health.chatbot)}
                <span className={health.chatbot === 'online' ? 'text-green-400' : 'text-red-400'}>
                  {health.chatbot === 'online' ? 'Online' : health.chatbot === 'checking' ? '...' : 'Offline'}
                </span>
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
