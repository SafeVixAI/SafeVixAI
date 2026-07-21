'use client';

// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
import React from 'react';


import { useEffect } from 'react';
import { ShieldAlert } from 'lucide-react';
import { logClientError } from '@/lib/client-logger';

export default function SOSError({ error, reset }: { error: Error; reset: () => void }) {
  useEffect(() => { logClientError('SOS page crashed:', error) }, [error]);
  return (
    <div className="flex flex-col items-center justify-center min-h-screen p-6 text-center">
      <ShieldAlert className="w-16 h-16 text-emergency mb-4" />
      <h1 className="text-xl font-bold mb-2">Emergency Service Unavailable</h1>
      <p className="text-text-2 mb-6 max-w-md">The SOS system encountered an error. Call 112 immediately for police or ambulance.</p>
      <div className="flex flex-col sm:flex-row gap-4">
        <a href="tel:112" className="px-8 py-3 bg-emergency text-white rounded-full font-bold text-lg hover:bg-emergency/90 transition-colors" aria-label="Call 112 emergency services">
          CALL 112 NOW
        </a>
        <button onClick={reset} className="px-6 py-3 bg-surface-3 text-text-1 rounded-full font-semibold hover:bg-surface-4 transition-colors">
          Try Again
        </button>
      </div>
    </div>
  );
}