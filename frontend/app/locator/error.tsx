// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
import React from 'react';

'use client';

import { useEffect } from 'react';
import { Navigation, Phone, RotateCcw } from 'lucide-react';
import { logClientError } from '@/lib/client-logger';

export default function LocatorError({ error, reset }: { error: Error; reset: () => void }) {
  useEffect(() => { logClientError('Locator page crashed:', error) }, [error]);
  return (
    <div className="flex flex-col items-center justify-center min-h-screen p-6 text-center">
      <Navigation className="w-16 h-16 text-warning mb-4" />
      <h1 className="text-xl font-bold mb-2">Navigation Unavailable</h1>
      <p className="text-text-2 mb-6 max-w-md">The locator service encountered an error. Your GPS may still work — try refreshing.</p>
      <div className="flex flex-col sm:flex-row gap-3">
        <a href="tel:112" aria-label="Call 112 emergency services" className="flex items-center gap-2 px-6 py-3 bg-red-600 text-white rounded-full font-bold hover:bg-red-500 transition-colors">
          <Phone size={18} />
          CALL 112
        </a>
        <button onClick={reset} className="flex items-center gap-2 px-6 py-3 bg-brand text-white rounded-full font-semibold hover:bg-brand/90 transition-colors">
          <RotateCcw size={18} />
          Reload Locator
        </button>
      </div>
    </div>
  );
}
