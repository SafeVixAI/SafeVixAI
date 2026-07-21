'use client';

// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team


import React, { useState, useEffect } from 'react';
import { Navigation, ShieldAlert, X } from 'lucide-react';
import { useAppStore } from '@/lib/store';

export const GPS_CONSENT_KEY = 'svai-gps-consent-v1';

export default function GpsConsent() {
  const [show, setShow] = useState(false);
  const setLocationTracking = useAppStore((s) => s.setLocationTracking);

  useEffect(() => {
    /* istanbul ignore next */
    if (typeof window === 'undefined') return;
    if (process.env.NODE_ENV !== 'production' && window.localStorage.getItem('__E2E_SKIP_AUTH__') === 'true') return;
    const consent = window.localStorage.getItem(GPS_CONSENT_KEY);
    if (!consent) {
      // Show GPS consent banner after a short delay (separated from cookie banner)
      const timer = setTimeout(() => setShow(true), 3500);
      return () => clearTimeout(timer);
    }
  }, []);

  const handleConsent = (granted: boolean) => {
    setShow(false);
    /* istanbul ignore next */
    if (typeof window === 'undefined') return;
    window.localStorage.setItem(GPS_CONSENT_KEY, granted ? 'granted' : 'denied');
    setLocationTracking(granted);
  };

  if (!show) return null;

  return (
    <div role="alert" aria-live="polite" className="fixed bottom-6 left-6 right-6 md:left-8 md:right-auto md:max-w-md z-[9999] animate-fade-in-up">
      <div className="relative overflow-hidden rounded-[2rem] p-6 bg-surface-1/80 dark:bg-surface-1/65 backdrop-blur-3xl border border-brand/20 shadow-2xl shadow-surface-3/50 dark:shadow-none flex flex-col gap-4">
        {/* Decorative top border highlight */}
        <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-red-400 via-orange-500 to-yellow-400" />

        <div className="flex items-start gap-4">
          <div className="w-10 h-10 rounded-xl bg-orange-500/10 border border-orange-500/20 flex items-center justify-center shrink-0 text-orange-500">
            <Navigation size={20} className="rotate-45" />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-black text-text-1 uppercase tracking-tight font-space flex items-center gap-1.5">
                Location Privacy
              </h3>
              <button 
                onClick={() => handleConsent(false)}
                aria-label="Dismiss location banner"
                className="text-text-3 hover:text-text-1 p-1 rounded-lg hover:bg-surface-3 transition-colors shrink-0"
              >
                <X size={16} />
              </button>
            </div>
            <p className="text-[11px] font-medium text-text-2 mt-1.5 leading-relaxed">
              SafeVixAI requests live GPS authorization to support <strong>Emergency SOS dispatch</strong>, offline nearby hospital locating, and hazardous road alerts under the <strong>Indian DPDP Act 2023</strong>. Your real-time path remains fully private and encrypted.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3 pt-2">
          <span className="flex items-center gap-1 text-[9px] font-bold text-text-3 uppercase tracking-wider font-space mr-auto">
            <ShieldAlert size={12} className="text-orange-500" />
            Consent Required
          </span>
          
          <button
            onClick={() => handleConsent(false)}
            className="px-4 py-2 border border-border text-text-2 hover:text-text-1 hover:border-text-2 rounded-xl text-[10px] font-bold uppercase tracking-wider font-space active:scale-95 transition-all"
          >
            Restrict
          </button>
          
          <button
            onClick={() => handleConsent(true)}
            className="px-5 py-2 bg-gradient-to-r from-orange-500 to-red-500 text-white rounded-xl text-[10px] font-black uppercase tracking-wider font-space shadow-lg hover:brightness-110 active:scale-95 transition-all"
          >
            Authorize
          </button>
        </div>
      </div>
    </div>
  );
}