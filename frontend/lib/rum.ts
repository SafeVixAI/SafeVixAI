// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

// frontend/lib/rum.ts — Real User Monitoring (Core Web Vitals + custom metrics)
// Logs performance data to console in dev; can be wired to analytics in prod.
'use client';

export function initRUM() {
  /* istanbul ignore next */
  if (typeof window === 'undefined') return;

  try {
    // LCP — Largest Contentful Paint
    const lcpObs = new PerformanceObserver((list) => {
      const entries = list.getEntries();
      const last = entries[entries.length - 1];
      reportMetric('LCP', last.startTime);
    });
    lcpObs.observe({ type: 'largest-contentful-paint', buffered: true });

    // FID/INP — First Input Delay / Interaction to Next Paint
    const fidObs = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        const timing = entry as unknown as { processingStart: number; startTime: number };
        reportMetric('FID', timing.processingStart - timing.startTime);
      }
    });
    fidObs.observe({ type: 'first-input', buffered: true });

    // CLS — Cumulative Layout Shift
    let clsValue = 0;
    const clsObs = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        const shift = entry as unknown as { hadRecentInput?: boolean; value?: number };
        /* istanbul ignore next */
        if (!shift.hadRecentInput) {
          clsValue += shift.value ?? 0;
        }
      }
      reportMetric('CLS', clsValue);
    });
    clsObs.observe({ type: 'layout-shift', buffered: true });

    // Navigation Timing — TTFB, DOM Complete, Load
    /* istanbul ignore next */
    if (performance.getEntriesByType('navigation').length > 0) {
      const nav = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
      reportMetric('TTFB', nav.responseStart - nav.requestStart);
      reportMetric('DOM_LOAD', nav.domContentLoadedEventEnd - nav.fetchStart);
      reportMetric('FULL_LOAD', nav.loadEventEnd - nav.fetchStart);
    }
  } catch {
    // Performance API not supported — degrade gracefully
  }
}

function reportMetric(name: string, value: number) {
  if (process.env.NODE_ENV === 'development') {
    console.log(`[RUM] ${name}: ${value.toFixed(2)}ms`);
  }
}
