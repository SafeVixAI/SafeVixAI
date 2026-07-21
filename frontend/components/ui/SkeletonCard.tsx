'use client';

// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team


import React from 'react';

interface SkeletonCardProps {
  lines?: number;
  hasIcon?: boolean;
  hasButton?: boolean;
}

export function SkeletonCard({ lines = 3, hasIcon = true, hasButton = false }: SkeletonCardProps) {
  return (
    <div className="border border-[var(--border)] rounded-[var(--r-lg)] bg-[var(--surface-1)] shadow-[var(--shadow-card)] p-5 flex flex-col gap-4 overflow-hidden relative">
      <div className="flex items-start gap-4">
        {hasIcon && (
          <div className="w-10 h-10 rounded-xl sv-skeleton shrink-0" />
        )}
        <div className="flex-1 flex flex-col gap-2.5 mt-1.5">
          <div className="h-4 w-2/3 rounded sv-skeleton" />
          <div className="h-3 w-1/3 rounded sv-skeleton" />
        </div>
      </div>
      
      <div className="flex flex-col gap-2 mt-2">
        {Array.from({ length: lines }).map((_, i) => (
          <div 
            key={i} 
            className="h-3 rounded sv-skeleton" 
            style={{ width: i === lines - 1 ? '50%' : '100%' }}
          />
        ))}
      </div>

      {hasButton && (
        <div className="h-9 w-28 rounded-lg sv-skeleton mt-2 self-start" />
      )}
    </div>
  );
}