'use client';

// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
import React from 'react';


import { memo } from 'react'
import { Inbox, type LucideIcon } from 'lucide-react'
import { cn } from '@/lib/utils'

interface EmptyStateProps {
  icon?: LucideIcon
  title: string
  description?: string
  action?: {
    label: string
    onClick: () => void
  }
  className?: string
}

export const EmptyState = memo(function EmptyState({
  icon: Icon = Inbox,
  title,
  description,
  action,
  className,
}: EmptyStateProps) {
  return (
    <div
      role="status"
      aria-label={title}
      className={cn(
        'flex w-full flex-col items-center justify-center py-12 text-center',
        className,
      )}
    >
      <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-surface-2">
        <Icon size={24} className="text-text-3" />
      </div>
      <h3 className="text-sm font-bold uppercase tracking-[0.06em] text-text-1">
        {title}
      </h3>
      {description && (
        <p className="mt-2 max-w-[280px] text-xs leading-relaxed text-text-3">
          {description}
        </p>
      )}
      {action && (
        <button
          onClick={action.onClick}
          className="mt-4 rounded-[6px] border border-brand-light/25 bg-brand-dim px-4 py-2 text-xs font-semibold text-brand-light transition-all hover:bg-brand/15"
        >
          {action.label}
        </button>
      )}
    </div>
  )
})