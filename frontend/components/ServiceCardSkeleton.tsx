'use client';

// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team


import React, { memo } from 'react';

/**
 * ServiceCardSkeleton — Shimmer loading placeholder for ServiceCard
 * Co-located with ServiceCard for feature-specific loading states
 */
const ServiceCardSkeleton = memo(function ServiceCardSkeleton() {
  return (
    <div className="rounded-xl border border-border bg-surface-2 p-4 space-y-3">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-lg skeleton" />
        <div className="flex-1 space-y-2">
          <div className="h-3.5 w-3/4 skeleton rounded-full" />
          <div className="h-2.5 w-1/2 skeleton rounded-full" />
        </div>
      </div>
      <div className="space-y-2">
        <div className="h-2.5 w-full skeleton rounded-full" />
        <div className="h-2.5 w-2/3 skeleton rounded-full" />
      </div>
      <div className="flex items-center justify-between pt-1">
        <div className="h-2 w-16 skeleton rounded-full" />
        <div className="h-2 w-12 skeleton rounded-full" />
      </div>
    </div>
  );
});

export default ServiceCardSkeleton;