'use client';

// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team


import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { ShieldCheck, Info, X } from 'lucide-react';
import { useAppStore } from '@/lib/store';
import { ANALYTICS_CONSENT_KEY } from '@/lib/analytics-provider';
import posthog from 'posthog-js';

export default function CookieConsent() {
  const [show, setShow] = useState(false);
  const setAnalyticsOptIn = useAppStore((s) => s.setAnalyticsOptIn);

  useEffect(() => {
    /* istanbul ignore next */
    if (typeof window === 'undefined') return;
    if (process.env.NODE_ENV !== 'production' && window.localStorage.getItem('__E2E_SKIP_AUTH__') === 'true') return;
    const consent = window.localStorage.getItem(ANALYTICS_CONSENT_KEY);
    if (!consent) {
      // Show banner if no consent choice has been recorded yet
      const timer = setTimeout(() => setShow(true), 2000);
      return () => clearTimeout(timer);
    }
  }, []);

  const handleConsent = (granted: boolean) => {
    setShow(false);
    /* istanbul ignore next */
    if (typeof window === 'undefined') return;
    window.localStorage.setItem(ANALYTICS_CONSENT_KEY, granted ? 'granted' : 'denied');
    setAnalyticsOptIn(granted);
    if (granted) {
      posthog.opt_in_capturing();
    } else {
      posthog.opt_out_capturing();
    }
  };

  if (!show) return null;

  return (
    <div className="fixed bottom-6 left-6 right-6 md:left-auto md:right-8 md:max-w-md z-[9999] animate-fade-in-up">
      <div className="relative overflow-hidden rounded-[2rem] p-6 bg-surface-1/80 dark:bg-surface-1/65 backdrop-blur-3xl border border-brand/20 shadow-2xl shadow-surface-3/50 dark:shadow-none flex flex-col gap-4">
        {/* Decorative subtle top border highlight */}
        <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-brand-light via-brand to-brand-light" />

        <div className="flex items-start gap-4">
          <div className="w-10 h-10 rounded-xl bg-brand/10 border border-brand/20 flex items-center justify-center shrink-0 text-brand-light">
            <ShieldCheck size={20} />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-black text-text-1 uppercase tracking-tight font-space">Privacy & Consent</h3>
              <button 
                onClick={() => handleConsent(false)}
                aria-label="Dismiss banner"
                className="text-text-3 hover:text-text-1 p-1 rounded-lg hover:bg-surface-3 transition-colors shrink-0"
              >
                <X size={16} />
              </button>
            </div>
            <p className="text-[11px] font-medium text-text-2 mt-1.5 leading-relaxed">
              SafeVixAI uses anonymous PostHog telemetry to improve emergency geocoding, SOS latency, and offline map caching under the <strong>DPDP Act 2023</strong>. No personal location history is stored without active consent.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3 pt-2">
          <Link 
            href="/privacy" 
            className="flex items-center gap-1.5 text-[9px] font-bold text-text-3 hover:text-text-1 uppercase tracking-wider font-space mr-auto"
          >
            <Info size={12} />
            View Policy
          </Link>
          
          <button
            onClick={() => handleConsent(false)}
            className="px-4 py-2 border border-border text-text-2 hover:text-text-1 hover:border-text-2 rounded-xl text-[10px] font-bold uppercase tracking-wider font-space active:scale-95 transition-all"
          >
            Decline
          </button>
          
          <button
            onClick={() => handleConsent(true)}
            className="px-5 py-2 bg-brand dark:bg-brand-light text-white dark:text-text-1 rounded-xl text-[10px] font-black uppercase tracking-wider font-space shadow-lg hover:brightness-110 active:scale-95 transition-all"
          >
            Accept
          </button>
        </div>
      </div>
    </div>
  );
}