// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

'use client';

import React from 'react';
import { Download, X, RotateCcw } from 'lucide-react';
import { useServiceWorkerUpdate } from '@/hooks/useServiceWorkerUpdate';

export default function PwaUpdatePrompt() {
  var { updateAvailable, applyUpdate, dismissUpdate } = useServiceWorkerUpdate();

  if (!updateAvailable) return null;

  return (
    <div
      role="alert"
      className="fixed bottom-4 left-1/2 -translate-x-1/2 z-50 w-[90vw] max-w-md px-4 py-3 bg-slate-800/95 backdrop-blur-sm border border-slate-700/40 rounded-xl shadow-2xl flex items-center justify-between gap-3 text-sm"
    >
      <div className="flex items-center gap-2 min-w-0">
        <RotateCcw className="w-4 h-4 shrink-0 text-emerald-400" />
        <span className="text-slate-200 truncate">
          <strong>New version available</strong>
          <span className="text-slate-400 ml-1">Update to get the latest features</span>
        </span>
      </div>
      <div className="flex items-center gap-2 shrink-0">
        <button
          onClick={applyUpdate}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-medium rounded-lg transition-colors"
        >
          <Download className="w-3.5 h-3.5" />
          Update
        </button>
        <button
          onClick={dismissUpdate}
          className="p-1.5 hover:bg-white/10 rounded-lg transition-colors text-slate-400 hover:text-slate-200"
          aria-label="Dismiss"
        >
          <X className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}
