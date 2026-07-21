'use client';

// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
import React from 'react';


import { useEffect } from 'react';
import Link from 'next/link';
import { AlertTriangle, Home, Phone, RefreshCw } from 'lucide-react';
import { logClientError } from '@/lib/client-logger';

export default function ResetPasswordError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    logClientError('ResetPassword route error boundary caught an error', {
      message: error.message,
      digest: error.digest,
    });
  }, [error]);

  return (
    <main className="min-h-screen bg-bg text-text-1 flex items-center justify-center px-6">
      <section className="w-full max-w-xl border border-red-500/25 bg-red-950/20 rounded-lg p-6 shadow-2xl">
        <div className="mb-6 rounded-md border border-emergency/30 bg-emergency/10 p-4 text-center">
          <p className="text-sm font-bold text-emergency">Emergency? Call 112 immediately</p>
          <a
            href="tel:112"
            className="mt-2 inline-flex items-center gap-2 rounded-md bg-emergency px-6 py-2 text-sm font-bold text-white transition hover:bg-emergency/90"
            aria-label="Call 112 emergency services"
          >
            <Phone aria-hidden="true" size={16} />
            CALL 112
          </a>
        </div>

        <div className="flex items-start gap-4">
          <div className="mt-1 rounded-full bg-red-500/15 p-3 text-red-300">
            <AlertTriangle aria-hidden="true" size={24} />
          </div>
          <div className="space-y-3">
            <p className="text-xs uppercase tracking-[0.24em] text-red-200/70">System Recovery</p>
            <h1 className="text-2xl font-black tracking-tight">Reset Password error</h1>
            <p className="text-sm leading-6 text-text-3">
              The password reset screen failed to render. Please try again or return home.
            </p>
            {error.digest && (
              <p className="font-mono text-xs text-text-2">Digest: {error.digest}</p>
            )}
            <div className="flex flex-wrap gap-3 pt-2">
              <button
                type="button"
                onClick={reset}
                className="inline-flex min-h-11 items-center gap-2 rounded-md bg-red-400 px-4 text-sm font-bold text-bg transition hover:bg-red-300"
              >
                <RefreshCw aria-hidden="true" size={16} />
                Try again
              </button>
              <Link
                href="/"
                className="inline-flex min-h-11 items-center gap-2 rounded-md border border-border-md px-4 text-sm font-bold text-text-1 transition hover:bg-white/10"
              >
                <Home aria-hidden="true" size={16} />
                Home
              </Link>
            </div>
          </div>
        </div>
      </section>
    </main>
  );
}