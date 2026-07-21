// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
import React from 'react';

export default function Loading() {
  return (
    <div role="status" aria-live="polite" className="flex min-h-screen flex-col items-center justify-center bg-bg gap-4 px-6">
      <span className="sr-only">Loading guide</span>
      <div className="h-12 w-12 animate-pulse rounded-full bg-brand/30" />
      <div className="h-4 w-48 animate-pulse rounded bg-white/10" />
    </div>
  );
}
