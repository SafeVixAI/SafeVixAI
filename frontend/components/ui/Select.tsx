'use client';

// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
import React from 'react';


import { ChevronDown } from 'lucide-react'
import { cn } from '@/lib/utils'

interface SelectOption {
  value: string
  label: string
}

interface SelectProps {
  options: SelectOption[]
  value: string
  onChange: (_value: string) => void
  label?: string
  placeholder?: string
  error?: string
  ariaLabel?: string
  className?: string
}

export function Select({
  options,
  value,
  onChange,
  label,
  placeholder = 'Select...',
  error,
  ariaLabel,
  className,
}: SelectProps) {
  const id = label ? label.toLowerCase().replace(/\s+/g, '-') : undefined

  return (
    <div className={cn('flex flex-col gap-1.5', className)}>
      {label && (
        <label
          htmlFor={id}
          className="text-[11px] font-semibold uppercase tracking-[0.08em] text-text-2"
        >
          {label}
        </label>
      )}
      <div className="relative">
        <select
          id={id}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          aria-label={ariaLabel ?? label}
          className={cn(
            'w-full appearance-none rounded-[6px] border bg-surface-2 px-3 py-2.5 pr-10 text-sm text-text-1 transition-all outline-none',
            'border-border focus:border-brand-light/50 focus:ring-3 focus:ring-brand-light/12',
            error && 'border-emergency focus:border-emergency/50 focus:ring-emergency/12',
            !value && 'text-text-3',
          )}
        >
          {placeholder && (
            <option value="" disabled>
              {placeholder}
            </option>
          )}
          {options.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
        <ChevronDown
          size={16}
          className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-text-3"
        />
      </div>
      {error && (
        <p className="text-xs text-text-red" role="alert">
          {error}
        </p>
      )}
    </div>
  )
}