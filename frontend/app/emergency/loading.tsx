// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
import React from 'react';

export default function EmergencyLoading() {
  return (
    <div className="flex min-h-[80vh] flex-col gap-6 p-4 md:p-6">
      <div className="flex items-center gap-3">
        <div className="h-10 w-10 animate-pulse rounded-full bg-red-500/20" />
        <div className="space-y-2">
          <div className="h-5 w-40 animate-pulse rounded bg-white/10" />
          <div className="h-3 w-24 animate-pulse rounded bg-white/5" />
        </div>
      </div>
      <div className="h-[50vh] w-full animate-pulse rounded-xl bg-white/5" />
      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="h-24 animate-pulse rounded-lg bg-white/5" />
        ))}
      </div>
    </div>
  );
}
