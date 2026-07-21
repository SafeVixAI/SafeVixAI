// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
import React from 'react';

export default function AssistantLoading() {
  return (
    <div className="flex min-h-[80vh] flex-col p-4 md:p-6">
      <div className="mb-4 flex items-center gap-3">
        <div className="h-10 w-10 animate-pulse rounded-full bg-brand/20" />
        <div className="space-y-2">
          <div className="h-5 w-48 animate-pulse rounded bg-white/10" />
          <div className="h-3 w-32 animate-pulse rounded bg-white/5" />
        </div>
      </div>
      <div className="flex-1 space-y-4 overflow-y-auto">
        {[...Array(3)].map((_, i) => (
          <div key={i} className={`flex ${i % 2 === 0 ? 'justify-start' : 'justify-end'}`}>
            <div className={`h-16 animate-pulse rounded-2xl bg-white/5 ${i % 2 === 0 ? 'w-3/4' : 'w-1/2'}`} />
          </div>
        ))}
      </div>
      <div className="mt-4 h-12 w-full animate-pulse rounded-xl bg-white/5" />
    </div>
  );
}
