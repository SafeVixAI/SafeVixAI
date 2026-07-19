// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
import React from 'react';

import Link from 'next/link';

export default function NotFound() {
  return (
    <main className="min-h-screen bg-bg text-text-1 flex items-center justify-center px-6">
      <section className="w-full max-w-xl border border-border-md rounded-lg p-6 shadow-2xl">
        <div className="flex items-start gap-4">
          <div className="mt-1 rounded-full bg-amber-500/15 p-3 text-amber-300">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
              <circle cx="12" cy="12" r="10" />
              <path d="M12 8v4M12 16h.01" strokeLinecap="round" />
            </svg>
          </div>
          <div className="space-y-3">
            <p className="text-xs uppercase tracking-[0.24em] text-amber-200/70">404 — Page Not Found</p>
            <h1 className="text-2xl font-black tracking-tight">This page does not exist</h1>
            <p className="text-sm leading-6 text-text-3">
              The page you are looking for may have been moved, deleted, or never existed.
              Use the navigation menu to find what you need.
            </p>
            <div className="flex flex-wrap gap-3 pt-2">
              <Link
                href="/"
                className="inline-flex min-h-11 items-center gap-2 rounded-md bg-brand px-4 text-sm font-bold text-bg transition hover:bg-brand/80"
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
                  <path d="M3 9.5L12 3l9 6.5V20a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V9.5z" strokeLinecap="round" strokeLinejoin="round" />
                  <path d="M9 21V12h6v9" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
                Go Home
              </Link>
              <Link
                href="/emergency"
                className="inline-flex min-h-11 items-center gap-2 rounded-md border border-red-500/30 px-4 text-sm font-bold text-red-300 transition hover:bg-red-950/30"
              >
                Emergency Services
              </Link>
            </div>
          </div>
        </div>
      </section>
    </main>
  );
}
