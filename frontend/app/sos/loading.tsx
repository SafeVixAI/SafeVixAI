// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
import React from 'react';

export default function SosLoading() {
  return (
    <div className="flex min-h-[80vh] flex-col items-center justify-center gap-8 p-6">
      <div className="flex flex-col items-center gap-4">
        <div className="h-24 w-24 animate-pulse rounded-full bg-red-500/20" />
        <div className="h-6 w-48 animate-pulse rounded bg-white/10" />
        <div className="h-3 w-32 animate-pulse rounded bg-white/5" />
      </div>
      <div className="h-12 w-48 animate-pulse rounded-full bg-red-500/10" />
    </div>
  );
}
