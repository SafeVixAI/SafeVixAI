'use client';

// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
import React from 'react';


import dynamic from 'next/dynamic';
import { Loader2 } from 'lucide-react';

const LocationPicker = dynamic(() => import('./LocationPickerInner'), {
  ssr: false,
  loading: () => (
    <div className="w-full h-[300px] bg-surface-2 rounded-xl flex items-center justify-center border border-border">
      <div className="flex flex-col items-center gap-3">
        <Loader2 size={24} className="animate-spin text-brand" />
        <span className="text-[10px] font-semibold uppercase tracking-widest text-text-3">Loading Map...</span>
      </div>
    </div>
  ),
});

export default LocationPicker;