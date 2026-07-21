'use client';

// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
import React from 'react';


import { useAppStore, ConnectivityState } from '@/lib/store';

const CONFIG: Record<ConnectivityState, { label: string; color: string }> = {
  'online':     { label: 'Live',    color: 'sv-conn-online' },
  'cached':     { label: 'Cached',  color: 'sv-conn-cached' },
  'offline':    { label: 'Offline', color: 'sv-conn-offline' },
  'ai-offline': { label: 'AI Active', color: 'sv-conn-ai' },
};

interface Props {
  className?: string;
}

export function ConnectivityBadge({ className = '' }: Props) {
  const connectivity = useAppStore((s) => s.connectivity);
  const { label, color } = CONFIG[connectivity];

  return (
    <span
      role="status"
      aria-live="polite"
      aria-label={`Connectivity: ${label}`}
      className={`sv-conn-badge ${color} ${className}`}
    >
      <span className="sv-conn-dot" aria-hidden="true" />
      {label}
    </span>
  );
}