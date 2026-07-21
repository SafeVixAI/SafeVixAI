'use client';

// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
import React from 'react';


import { memo } from 'react'
import { AlertTriangle, RotateCw, type LucideIcon } from 'lucide-react'
import { cn } from '@/lib/utils'

interface ErrorStateProps {
  icon?: LucideIcon
  message: string
  retry?: () => void
  fallbackLabel?: string
  className?: string
}

export const ErrorState = memo(function ErrorState({
  icon: Icon = AlertTriangle,
  message,
  retry,
  fallbackLabel,
  className,
}: ErrorStateProps) {
  return (
    <div
      role="alert"
      className={cn(
        'flex w-full flex-col items-center justify-center rounded-[8px] border border-emergency-dim bg-surface-1 py-10 text-center',
        className,
      )}
    >
      <div className="mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-emergency-dim">
        <Icon size={22} className="text-emergency" />
      </div>
      <p className="max-w-[300px] text-sm font-medium text-text-1">{message}</p>
      {retry && (
        <button
          onClick={retry}
          className="mt-4 inline-flex items-center gap-2 rounded-[6px] border border-emergency/40 bg-emergency-dim px-4 py-2 text-xs font-semibold text-emergency transition-all hover:bg-emergency/20"
        >
          <RotateCw size={14} />
          {fallbackLabel || 'Try Again'}
        </button>
      )}
    </div>
  )
})