'use client';

// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team


import React from 'react';
import { useSplitTextEntry } from '@/hooks/useSplitTextEntry';

interface TerminalHeaderProps {
  title: string;
  subtitle?: string;
  status?: 'online' | 'offline' | 'emergency';
  rightElement?: React.ReactNode;
}

export function TerminalHeader({
  title,
  subtitle,
  status = 'online',
  rightElement,
}: TerminalHeaderProps) {
  const titleRef = useSplitTextEntry();
  const statusLabel = status === 'emergency' ? 'Emergency Active' : status === 'offline' ? 'Offline' : 'Sentinel Active';

  return (
    <div className="sv-terminal-header">
      <div className="flex items-center gap-3">
        <div className="flex flex-col">
          <div className="flex items-center gap-2">
            <h1 ref={titleRef} className="sv-terminal-overline text-text-1">
              {title}
            </h1>
            {status === 'online' && (
              <span className="sv-status-dot" title="System Online" />
            )}
            {status === 'emergency' && (
              <span className="flex h-1.5 w-1.5 rounded-full bg-emergency animate-ping" title="Emergency Active" />
            )}
            {status === 'offline' && (
              <span className="flex h-1.5 w-1.5 rounded-full bg-text-3" title="System Offline" />
            )}
            <span className="hidden sm:inline text-micro font-medium text-brand-light">{statusLabel}</span>
          </div>
          {subtitle && (
            <span className="text-caption font-medium tracking-[0.05em] text-text-3 uppercase mt-0.5">
              {subtitle}
            </span>
          )}
        </div>
      </div>
      {rightElement && (
        <div className="flex items-center">
          {rightElement}
        </div>
      )}
    </div>
  );
}