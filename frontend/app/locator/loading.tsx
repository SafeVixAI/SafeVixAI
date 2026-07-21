// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
import React from 'react';

export default function LocatorLoading() {
  return (
    <div className="flex min-h-[80vh] flex-col gap-6 p-4 md:p-6">
      <div className="flex items-center gap-3">
        <div className="h-10 w-10 animate-pulse rounded-full bg-brand/20" />
        <div className="space-y-2">
          <div className="h-5 w-36 animate-pulse rounded bg-white/10" />
          <div className="h-3 w-20 animate-pulse rounded bg-white/5" />
        </div>
      </div>
      <div className="h-[55vh] w-full animate-pulse rounded-xl bg-white/5" />
      <div className="flex gap-2">
        <div className="h-10 flex-1 animate-pulse rounded-lg bg-white/5" />
        <div className="h-10 w-10 animate-pulse rounded-lg bg-white/5" />
      </div>
    </div>
  );
}
