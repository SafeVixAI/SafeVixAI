'use client';

// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team


import React, { memo } from 'react';

const SkeletonCard = memo(function SkeletonCard({ className = "" }: { className?: string }) {
  return (
    <div className={`rounded-lg border border-border-md dark:border-white/5 bg-white dark:bg-white/5 p-6 animate-pulse ${className}`}>
      <div className="flex items-center gap-4 mb-4">
        <div className="w-10 h-10 rounded-xl skeleton" />
        <div className="space-y-2">
          <div className="h-3 w-24 skeleton rounded-full" />
          <div className="h-2 w-16 skeleton rounded-full" />
        </div>
      </div>
      <div className="space-y-2">
        <div className="h-2 w-full skeleton rounded-full" />
        <div className="h-2 w-[80%] skeleton rounded-full" />
      </div>
    </div>
  );
});

export default SkeletonCard;