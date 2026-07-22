'use client';

// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
import React from 'react';


import { useEffect } from 'react';
import { MapPin, RotateCcw } from 'lucide-react';
import { logClientError } from '@/lib/client-logger';

export default function EmergencyError({ error, reset }: { error: Error; reset: () => void }) {
  useEffect(() => { logClientError('Emergency locator page crashed:', error) }, [error]);
  return (
    <div className="flex flex-col items-center justify-center min-h-screen p-6 text-center">
      <MapPin className="w-16 h-16 text-warning mb-4" />
      <h1 className="text-xl font-bold mb-2">Emergency Locator Unavailable</h1>
      <p className="text-text-2 mb-6 max-w-md">Could not load nearby emergency services. Please check your connection and try again.</p>
      <div className="flex flex-col sm:flex-row gap-4">
        <button onClick={reset} className="flex items-center gap-2 px-6 py-3 bg-brand text-white rounded-full font-semibold hover:bg-brand/90 transition-colors">
          <RotateCcw size={18} />
          Retry
        </button>
        <a href="tel:112" className="px-8 py-3 bg-emergency text-white rounded-full font-bold hover:bg-emergency/90 transition-colors" aria-label="Call 112 emergency services">
          CALL 112
        </a>
      </div>
    </div>
  );
}