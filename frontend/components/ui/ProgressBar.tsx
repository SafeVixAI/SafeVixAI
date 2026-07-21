// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
import React from 'react';

import { cn } from '@/lib/utils'

interface ProgressBarProps {
  value?: number
  max?: number
  variant?: 'determinate' | 'indeterminate'
  color?: string
  className?: string
}

export function ProgressBar({
  value = 0,
  max = 100,
  variant = 'determinate',
  color,
  className,
}: ProgressBarProps) {
  const pct = Math.min(Math.max((value / max) * 100, 0), 100)

  return (
    <div
      role="progressbar"
      aria-valuenow={variant === 'determinate' ? pct : undefined}
      aria-valuemin={0}
      aria-valuemax={100}
      className={cn('h-1.5 w-full rounded-full bg-surface-3 overflow-hidden', className)}
    >
      <div
        className={cn(
          'h-full rounded-full transition-all duration-300',
          variant === 'indeterminate' ? 'animate-indeterminate w-1/2' : 'w-full'
        )}
        style={{
          width: variant === 'determinate' ? `${pct}%` : undefined,
          backgroundColor: color || 'var(--brand)',
        }}
      />
    </div>
  )
}
