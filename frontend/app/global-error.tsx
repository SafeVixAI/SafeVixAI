'use client';

// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
import React from 'react';


import { useEffect } from 'react';

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    try {
      fetch('/api/log', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          level: 'fatal',
          message: error.message,
          digest: error.digest,
        }),
      }).catch(() => undefined);
    } catch {
      // Error telemetry is best-effort; never throw from the global error boundary.
    }
  }, [error]);

  return (
    <html>
      <body className="bg-bg text-text-1">
        <main className="min-h-screen flex items-center justify-center px-6">
          <section className="w-full max-w-xl border border-red-500/25 bg-red-950/20 rounded-lg p-6 shadow-2xl">
            <div className="flex items-start gap-4">
              <div className="mt-1 rounded-full bg-red-500/15 p-3 text-red-300">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
                  <circle cx="12" cy="12" r="10" />
                  <path d="M12 8v4M12 16h.01" strokeLinecap="round" />
                </svg>
              </div>
              <div className="space-y-3">
                <p className="text-xs uppercase tracking-[0.24em] text-red-200/70">System Critical</p>
                <h1 className="text-2xl font-black tracking-tight">SafeVixAI encountered a critical error</h1>
                <p className="text-sm leading-6 text-text-3">
                  The application failed to load. Please refresh the page or try again later.
                  If the problem persists, contact support.
                </p>
                {error.digest && (
                  <p className="font-mono text-xs text-text-2">Error reference: {error.digest}</p>
                )}
                <div className="flex flex-wrap gap-3 pt-2">
                  <button
                    type="button"
                    onClick={reset}
                    className="inline-flex min-h-11 items-center gap-2 rounded-md bg-red-400 px-4 text-sm font-bold text-bg transition hover:bg-red-300"
                  >
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
                      <path d="M3 12a9 9 0 1 1 9 9" strokeLinecap="round" />
                      <path d="M3 3v6h6" strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                    Try Again
                  </button>
                  <button
                    type="button"
                    onClick={() => window.location.href = '/'}
                    className="inline-flex min-h-11 items-center gap-2 rounded-md border border-border-md px-4 text-sm font-bold text-text-1 transition hover:bg-white/10"
                  >
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
                      <path d="M3 9.5L12 3l9 6.5V20a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V9.5z" strokeLinecap="round" strokeLinejoin="round" />
                      <path d="M9 21V12h6v9" strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                    Home
                  </button>
                </div>
              </div>
            </div>
          </section>
        </main>
      </body>
    </html>
  );
}