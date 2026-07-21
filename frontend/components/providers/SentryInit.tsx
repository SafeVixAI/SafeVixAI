'use client';

// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team


import { useEffect } from 'react';

export function SentryInit() {
  useEffect(() => {
    const dsn = process.env.NEXT_PUBLIC_SENTRY_DSN;
    if (!dsn) return;

    const script = document.createElement('script');
    script.src = 'https://browser.sentry-cdn.com/8.0.0/bundle.tracing.replay.min.js';
    script.crossOrigin = 'anonymous';
    script.onload = () => {
      (window as any).Sentry.init({
        dsn,
        environment: process.env.NODE_ENV,
        tracesSampleRate: 0.1,
        replaysSessionSampleRate: 0.1,
        replaysOnErrorSampleRate: 1.0,
        integrations: [
          (window as any).Sentry.replayIntegration(),
        ],
      });
    };
    document.head.appendChild(script);
  }, []);

  return null;
}