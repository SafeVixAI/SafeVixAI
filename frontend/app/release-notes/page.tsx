// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

'use client';

import React, { useEffect, useState, useCallback } from 'react';
import { TerminalHeader } from '@/components/ui/TerminalHeader';
import { Shield, AlertTriangle, Loader2, RefreshCw } from 'lucide-react';
import { fetchReleases, type ReleaseSummary } from '@/lib/api/update-api';
import { logClientError } from '@/lib/client-logger';

type Channel = 'stable' | 'beta' | 'nightly' | 'all';

const CHANNELS: { key: Channel; label: string }[] = [
  { key: 'all', label: 'All' },
  { key: 'stable', label: 'Stable' },
  { key: 'beta', label: 'Beta' },
  { key: 'nightly', label: 'Nightly' },
];

export default function ReleaseNotesPage() {
  const [releases, setReleases] = useState<ReleaseSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [channel, setChannel] = useState<Channel>('all');
  const [page, setPage] = useState(1);
  const limit = 20;

  const load = useCallback(async function () {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchReleases(channel === 'all' ? undefined : channel, limit, (page - 1) * limit);
      setReleases(data);
    } catch (err) {
      setError('Failed to load release notes');
      logClientError('ReleaseNotesPage', err);
    } finally {
      setLoading(false);
    }
  }, [channel, page, limit]);

  useEffect(function () { load(); }, [load]);

  return (
    <main className="min-h-screen bg-slate-950 text-slate-200">
      <TerminalHeader />
      <div className="max-w-4xl mx-auto px-4 py-8">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Shield className="w-6 h-6 text-emerald-400" />
            Release Notes
          </h1>
          <button onClick={load} className="p-2 hover:bg-slate-800 rounded-lg transition-colors" aria-label="Refresh">
            <RefreshCw className={'w-4 h-4' + (loading ? ' animate-spin' : '')} />
          </button>
        </div>

        <div className="flex gap-2 mb-6">
          {CHANNELS.map(function (ch) {
            return (
              <button
                key={ch.key}
                onClick={function () { setChannel(ch.key); setPage(1); }}
                className={'px-4 py-1.5 rounded-lg text-sm font-medium transition-colors ' + (
                  channel === ch.key
                    ? 'bg-emerald-600/20 text-emerald-300 border border-emerald-600/40'
                    : 'bg-slate-800/50 text-slate-400 border border-slate-700/40 hover:bg-slate-700/50'
                )}
              >
                {ch.label}
              </button>
            );
          })}
        </div>

        {loading && (
          <div className="flex justify-center py-20" role="alert">
            <Loader2 className="w-8 h-8 animate-spin text-emerald-400" />
          </div>
        )}

        {error && (
          <div className="flex items-center gap-2 p-4 bg-red-900/20 border border-red-700/40 rounded-lg text-red-300" role="alert">
            <AlertTriangle className="w-5 h-5" />
            {error}
          </div>
        )}

        {!loading && !error && releases.length === 0 && (
          <div className="text-center py-20 text-slate-500">
            <Shield className="w-12 h-12 mx-auto mb-4 opacity-30" />
            <p className="text-lg">No releases found</p>
            <p className="text-sm mt-1">Try a different channel filter</p>
          </div>
        )}

        {!loading && !error && releases.map(function (r) {
          return (
            <div key={r.id} className="mb-4 p-4 bg-slate-900 border border-slate-800 rounded-lg">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <span className="font-mono font-bold text-emerald-400">v{r.version}</span>
                  <span className={
                    'text-xs px-2 py-0.5 rounded-full ' + (
                      r.channel === 'stable' ? 'bg-emerald-900/30 text-emerald-300 border border-emerald-700/40' :
                      r.channel === 'beta' ? 'bg-amber-900/30 text-amber-300 border border-amber-700/40' :
                      'bg-slate-800 text-slate-400 border border-slate-700'
                    )
                  }>
                    {r.channel}
                  </span>
                  {r.is_security && (
                    <span className="text-xs px-2 py-0.5 bg-red-900/30 text-red-300 border border-red-700/40 rounded-full">Security</span>
                  )}
                </div>
                <span className="text-xs text-slate-500">
                  {r.published_at ? new Date(r.published_at).toLocaleDateString() : 'Unpublished'}
                </span>
              </div>
              <div className="text-sm text-slate-300">{r.title}</div>
            </div>
          );
        })}
      </div>
    </main>
  );
}
