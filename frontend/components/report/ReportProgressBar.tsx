'use client';

// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team


import React from 'react';
import { Check } from 'lucide-react';

interface ReportProgressBarProps {
  currentStep: number; // 0-indexed
  totalSteps?: number;
}

const STEP_LABELS = ['Category', 'Location', 'Details', 'Contact', 'Review'];

export function ReportProgressBar({ currentStep, totalSteps = 5 }: ReportProgressBarProps) {
  return (
    <div className="w-full px-2">
      <div className="flex items-center justify-between relative">
        {/* Connecting line */}
        <div className="absolute top-4 left-0 right-0 h-0.5 bg-surface-3 z-0" />
        <div
          className="absolute top-4 left-0 h-0.5 bg-brand transition-all duration-500 z-0"
          style={{ width: `${(currentStep / (totalSteps - 1)) * 100}%` }}
        />

        {Array.from({ length: totalSteps }).map((_, i) => {
          const isCompleted = i < currentStep;
          const isActive = i === currentStep;
          const label = STEP_LABELS[i] ?? `Step ${i + 1}`;

          return (
            <div key={i} className="flex flex-col items-center relative z-10">
              {/* Circle */}
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold transition-all duration-300 ${
                  isCompleted
                    ? 'bg-brand text-white shadow-[0_0_12px_rgba(var(--brand-rgb,59,130,246),0.4)]'
                    : isActive
                    ? 'bg-brand text-white shadow-[0_0_16px_rgba(var(--brand-rgb,59,130,246),0.5)] scale-110'
                    : 'bg-surface-3 text-text-3'
                }`}
              >
                {isCompleted ? <Check size={14} strokeWidth={3} /> : i + 1}
              </div>

              {/* Label */}
              <span
                className={`mt-2 text-[10px] font-semibold uppercase tracking-wider whitespace-nowrap hidden sm:block ${
                  isActive ? 'text-brand-light' : isCompleted ? 'text-text-2' : 'text-text-3'
                }`}
              >
                {label}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}