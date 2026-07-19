// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
import React from 'react';

'use client';

import { useEffect } from 'react';
import Link from 'next/link';
import { AlertTriangle, Home, Phone, RefreshCw } from 'lucide-react';
import { logClientError } from '@/lib/client-logger';
import { useTranslation } from 'react-i18next';

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  const { t } = useTranslation('common');
  useEffect(() => {
    logClientError('App route error boundary caught an error', {
      message: error.message,
      digest: error.digest,
    });
  }, [error]);

  return (
    <main className="min-h-screen bg-bg text-text-1 flex items-center justify-center px-6">
      <section className="w-full max-w-xl border border-red-500/25 bg-red-950/20 rounded-lg p-6 shadow-2xl">
        {/* Emergency banner — always visible, even on non-emergency pages */}
        <div className="mb-6 rounded-md border border-emergency/30 bg-emergency/10 p-4 text-center">
          <p className="text-sm font-bold text-emergency">
            {t('common.emergency_call_112', 'Emergency? Call 112 immediately')}
          </p>
          <a
            href="tel:112"
            className="mt-2 inline-flex items-center gap-2 rounded-md bg-emergency px-6 py-2 text-sm font-bold text-white transition hover:bg-emergency/90"
            aria-label={t('common.call_112_aria', 'Call 112 emergency services')}
          >
            <Phone aria-hidden="true" size={16} />
            {t('common.call_112_btn', 'CALL 112')}
          </a>
        </div>

        <div className="flex items-start gap-4">
          <div className="mt-1 rounded-full bg-red-500/15 p-3 text-red-300">
            <AlertTriangle aria-hidden="true" size={24} />
          </div>
          <div className="space-y-3">
            <p className="text-xs uppercase tracking-[0.24em] text-red-200/70">{t('common.system_recovery', 'System Recovery')}</p>
            <h1 className="text-2xl font-black tracking-tight">{t('common.recoverable_error_title', 'SafeVixAI hit a recoverable error')}</h1>
            <p className="text-sm leading-6 text-text-3">
              {t('common.recoverable_error_desc', 'The current screen failed to render safely. Your emergency shortcuts remain available from the home screen.')}
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
                {t('common.retry', 'Retry')}
              </button>
              <Link
                href="/"
                className="inline-flex min-h-11 items-center gap-2 rounded-md border border-border-md px-4 text-sm font-bold text-text-1 transition hover:bg-white/10"
              >
                <Home aria-hidden="true" size={16} />
                {t('common.home', 'Home')}
              </Link>
            </div>
          </div>
        </div>
      </section>
    </main>
  );
}
