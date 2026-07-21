'use client';

// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team


import React from 'react';

interface MapCoreProps {
  mapNodeRef: React.RefObject<HTMLDivElement | null>;
  status: 'loading' | 'ready' | 'error';
  statusMessage: string;
}

export function MapCore({ mapNodeRef, status, statusMessage }: MapCoreProps) {
  return (
    <>
      <div
        ref={mapNodeRef}
        role="application"
        aria-label="Interactive map. Use arrow keys to pan, plus and minus to zoom."
        tabIndex={0}
        className="absolute inset-0 h-full w-full overflow-hidden"
      />
      {status !== 'ready' && (
        <div className="pointer-events-none absolute inset-0 flex items-center justify-center bg-surface-1/85 backdrop-blur-[1px] z-[50]">
          <div className="rounded-lg border border-white/10 bg-surface-1/90 px-4 py-3 text-center shadow-2xl">
            <div className="text-[10px] font-semibold uppercase tracking-[0.22em] text-brand-light">
              {status === 'error' ? 'Map Offline' : 'Initializing Map'}
            </div>
            <div className="mt-2 text-sm font-semibold text-text-1">{statusMessage}</div>
          </div>
        </div>
      )}
    </>
  );
}