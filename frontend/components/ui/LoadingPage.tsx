// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
import React from 'react';

import { memo } from 'react'

interface LoadingPageProps {
  variant?: 'default' | 'chat' | 'map' | 'form' | 'grid' | 'emergency' | 'sos'
  iconBg?: string
}

function Skeleton({ className }: { className?: string }) {
  return <div className={`animate-pulse rounded bg-surface-2 ${className ?? ''}`} />
}

export const LoadingPage = memo(function LoadingPage({ variant = 'default', iconBg }: LoadingPageProps) {
  const iconClass = iconBg ?? 'bg-brand-dim'

  switch (variant) {
    case 'chat':
      return (
        <div aria-busy="true" role="status" aria-label="Loading messages" className="flex min-h-[80vh] flex-col p-4 md:p-6">
          <div className="mb-4 flex items-center gap-3">
            <Skeleton className="h-10 w-10 rounded-full" />
            <div className="space-y-2">
              <Skeleton className="h-5 w-48" />
              <Skeleton className="h-3 w-32" />
            </div>
          </div>
          <div className="flex-1 space-y-4 overflow-y-auto">
            {[...Array(3)].map((_, i) => (
              <div key={i} className={`flex ${i % 2 === 0 ? 'justify-start' : 'justify-end'}`}>
                <div className={`h-16 animate-pulse rounded-2xl bg-surface-2 ${i % 2 === 0 ? 'w-3/4' : 'w-1/2'}`} />
              </div>
            ))}
          </div>
          <Skeleton className="mt-4 h-12 w-full rounded-xl" />
        </div>
      )

    case 'map':
      return (
        <div aria-busy="true" role="status" aria-label="Loading map" className="flex min-h-[80vh] flex-col gap-6 p-4 md:p-6">
          <div className="flex items-center gap-3">
            <div className={`h-10 w-10 animate-pulse rounded-full ${iconClass}`} />
            <div className="space-y-2">
              <Skeleton className="h-5 w-36" />
              <Skeleton className="h-3 w-20" />
            </div>
          </div>
          <Skeleton className="h-[55vh] w-full rounded-xl" />
          <div className="flex gap-2">
            <Skeleton className="h-10 flex-1 rounded-lg" />
            <Skeleton className="h-10 w-10 rounded-lg" />
          </div>
        </div>
      )

    case 'form':
      return (
        <div aria-busy="true" role="status" aria-label="Loading form" className="flex min-h-[80vh] flex-col gap-6 p-4 md:p-6">
          <div className="flex items-center gap-3">
            <div className={`h-10 w-10 animate-pulse rounded-full ${iconClass}`} />
            <div className="space-y-2">
              <Skeleton className="h-5 w-36" />
              <Skeleton className="h-3 w-24" />
            </div>
          </div>
          <div className="space-y-4">
            <Skeleton className="h-10 rounded-lg" />
            <Skeleton className="h-10 rounded-lg" />
            <Skeleton className="h-32 rounded-lg" />
            <Skeleton className="h-10 w-32 rounded-lg" />
          </div>
        </div>
      )

    case 'grid':
      return (
        <div aria-busy="true" role="status" aria-label="Loading dashboard" className="flex min-h-[80vh] flex-col gap-6 p-4 md:p-6">
          <div className="flex items-center gap-3">
            <div className={`h-10 w-10 animate-pulse rounded-full ${iconClass}`} />
            <div className="space-y-2">
              <Skeleton className="h-5 w-44" />
              <Skeleton className="h-3 w-28" />
            </div>
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-3">
              <Skeleton className="h-10 rounded-lg" />
              <Skeleton className="h-10 rounded-lg" />
              <Skeleton className="h-32 rounded-lg" />
            </div>
            <Skeleton className="h-48 rounded-lg" />
          </div>
        </div>
      )

    case 'emergency':
      return (
        <div aria-busy="true" role="status" aria-label="Loading emergency" className="flex min-h-[80vh] flex-col gap-6 p-4 md:p-6">
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-3">
              <Skeleton className="h-10 w-10 rounded-full" />
              <div className="space-y-2">
                <Skeleton className="h-5 w-40" />
                <Skeleton className="h-3 w-24" />
              </div>
            </div>
          </div>
          <Skeleton className="h-[50vh] w-full rounded-xl" />
          <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
            {[...Array(4)].map((_, i) => (
              <Skeleton key={i} className="h-24 rounded-lg" />
            ))}
          </div>
        </div>
      )

    case 'sos':
      return (
        <div aria-busy="true" role="status" aria-label="Loading SOS" className="flex min-h-[80vh] flex-col items-center justify-center gap-8 p-6">
          <div className="flex flex-col items-center gap-4">
            <Skeleton className="h-24 w-24 rounded-full" />
            <Skeleton className="h-6 w-48" />
            <Skeleton className="h-3 w-32" />
          </div>
          <Skeleton className="h-12 w-48 rounded-full" />
        </div>
      )

    default:
      return (
        <div aria-busy="true" role="status" aria-label="Loading page" className="flex min-h-screen flex-col items-center justify-center gap-8 bg-bg px-6">
          <div className="flex flex-col items-center gap-6">
            <svg
              className="h-12 w-12 animate-pulse text-brand-light/30"
              viewBox="0 0 48 48"
              fill="none"
              aria-hidden="true"
            >
              <circle cx="24" cy="24" r="22" stroke="currentColor" strokeWidth="2" />
              <path d="M24 14v12M24 30v2" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
            </svg>
            <div className="space-y-2 text-center">
              <Skeleton className="mx-auto h-4 w-48" />
              <Skeleton className="mx-auto h-3 w-32" />
            </div>
          </div>
          <div className="flex gap-3">
            {[...Array(4)].map((_, i) => (
              <Skeleton key={i} className="h-20 w-20 rounded-xl" />
            ))}
          </div>
        </div>
      )
  }
})