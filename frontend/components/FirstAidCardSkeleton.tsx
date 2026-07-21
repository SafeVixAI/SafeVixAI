'use client';

// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team


import React, { memo } from 'react';

/**
 * FirstAidCardSkeleton — Shimmer placeholder for FirstAid guide cards
 */
const FirstAidCardSkeleton = memo(function FirstAidCardSkeleton() {
  return (
    <div className="rounded-xl border border-border bg-surface-2 p-5 space-y-3">
      <div className="flex items-center gap-3">
        <div className="w-12 h-12 rounded-xl skeleton" />
        <div className="flex-1 space-y-2">
          <div className="h-4 w-2/3 skeleton rounded-full" />
          <div className="h-2.5 w-1/3 skeleton rounded-full" />
        </div>
      </div>
      <div className="space-y-2 pt-1">
        <div className="h-2.5 w-full skeleton rounded-full" />
        <div className="h-2.5 w-5/6 skeleton rounded-full" />
        <div className="h-2.5 w-3/4 skeleton rounded-full" />
      </div>
    </div>
  );
});

export default FirstAidCardSkeleton;