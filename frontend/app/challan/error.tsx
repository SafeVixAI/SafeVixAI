'use client';

// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
import React from 'react';


import { useEffect } from 'react';
import Link from 'next/link';
import { Scale, Home, Phone, RefreshCw } from 'lucide-react';
import { logClientError } from '@/lib/client-logger';

export default function ChallanError({ error, reset }: { error: Error; reset: () => void }) {
  useEffect(() => { logClientError('Challan page crashed:', error) }, [error]);
  return (
    <main className="min-h-screen bg-bg text-text-1 flex items-center justify-center px-6">
      <section className="w-full max-w-xl border border-red-500/25 bg-red-950/20 rounded-lg p-6 shadow-2xl">
        <div className="mb-6 rounded-md border border-emergency/30 bg-emergency/10 p-4 text-center">
          <p className="text-sm font-bold text-emergency">Emergency? Call 112 immediately</p>
          <a href="tel:112" className="mt-2 inline-flex items-center gap-2 rounded-md bg-emergency px-6 py-2 text-sm font-bold text-white hover:bg-emergency/90" aria-label="Call 112"><Phone size={16} /> CALL 112</a>
        </div>
        <div className="flex items-start gap-4">
          <div className="mt-1 rounded-full bg-red-500/15 p-3 text-red-300"><Scale size={24} /></div>
          <div className="space-y-3">
            <p className="text-xs uppercase tracking-[0.24em] text-red-200/70">Challan Calculator</p>
            <h1 className="text-2xl font-black tracking-tight">Calculator unavailable</h1>
            <p className="text-sm leading-6 text-text-3">The fine calculation engine encountered an error. Try again or use the offline calculator.</p>
            <div className="flex flex-wrap gap-3 pt-2">
              <button onClick={reset} className="inline-flex min-h-11 items-center gap-2 rounded-md bg-red-400 px-4 text-sm font-bold text-bg hover:bg-red-300"><RefreshCw size={16} /> Retry</button>
              <Link href="/" className="inline-flex min-h-11 items-center gap-2 rounded-md border border-border-md px-4 text-sm font-bold text-text-1 hover:bg-white/10"><Home size={16} /> Home</Link>
            </div>
          </div>
        </div>
      </section>
    </main>
  );
}