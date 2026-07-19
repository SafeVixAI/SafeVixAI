// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
import React from 'react';

'use client';

import { useTranslation } from 'react-i18next';

export default function RootLoading() {
  const { t } = useTranslation('common');
  return (
    <div role="status" aria-live="polite" className="flex min-h-screen flex-col items-center justify-center bg-bg gap-8 px-6">
      <span className="sr-only">{t('loading_app', 'Loading SafeVixAI application')}</span>
      <div className="flex flex-col items-center gap-6">
        <svg
          className="h-12 w-12 animate-pulse"
          viewBox="0 0 48 48"
          fill="none"
          aria-hidden="true"
        >
          <circle cx="24" cy="24" r="22" stroke="currentColor" strokeWidth="2" className="text-brand/30" />
          <path d="M24 14v12M24 30v2" stroke="currentColor" strokeWidth="3" strokeLinecap="round" className="text-brand" />
        </svg>
        <div className="space-y-2 text-center">
          <div className="h-4 w-48 animate-pulse rounded bg-white/10" />
          <div className="h-3 w-32 animate-pulse rounded bg-white/5 mx-auto" />
        </div>
      </div>
      <div className="flex gap-3">
        {[...Array(4)].map((_, i) => (
          <div
            key={i}
            className="h-20 w-20 animate-pulse rounded-xl bg-white/5"
            style={{ animationDelay: `${i * 150}ms` }}
          />
        ))}
      </div>
    </div>
  );
}
