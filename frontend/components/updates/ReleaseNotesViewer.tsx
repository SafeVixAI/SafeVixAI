// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

'use client';

import React from 'react';
import { X, Shield } from 'lucide-react';
import type { ReleaseDetail } from '@/lib/api/update-api';

interface ReleaseNotesViewerProps {
  release: ReleaseDetail | null;
  onClose: () => void;
}

export default function ReleaseNotesViewer({ release, onClose }: ReleaseNotesViewerProps) {
  if (!release) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="w-full max-w-lg mx-4 max-h-[80vh] overflow-y-auto bg-slate-900 border border-slate-700/40 rounded-xl shadow-2xl">
        <div className="sticky top-0 bg-slate-900 border-b border-slate-700/40 px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Shield className="w-5 h-5 text-emerald-400" />
            <h2 className="font-bold text-slate-200">
              v{release.version}
              <span className="text-xs ml-2 px-2 py-0.5 rounded-full bg-slate-800 text-slate-400">
                {release.channel}
              </span>
            </h2>
          </div>
          <button onClick={onClose} className="p-1 hover:bg-slate-700 rounded-lg transition-colors" aria-label="Close">
            <X className="w-5 h-5 text-slate-400" />
          </button>
        </div>
        <div className="p-4">
          {release.release_notes_url && (
            <a
              href={release.release_notes_url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm text-emerald-400 hover:text-emerald-300 underline mb-3 inline-block"
            >
              View full release notes →
            </a>
          )}
          <div className="text-sm text-slate-300 whitespace-pre-wrap">
            {release.body || 'No release notes available for this version.'}
          </div>
          {release.checksum_sha256 && (
            <div className="mt-4 p-2 bg-slate-800 rounded-lg">
              <p className="text-xs text-slate-500 mb-1">SHA-256 Checksum</p>
              <code className="text-xs text-slate-400 break-all font-mono">{release.checksum_sha256}</code>
            </div>
          )}
          <div className="mt-3 text-xs text-slate-500">
            Published: {release.published_at ? new Date(release.published_at).toLocaleDateString() : 'Unpublished'}
            {release.asset_size_bytes && (
              <span className="ml-3">Size: {(release.asset_size_bytes / 1024 / 1024).toFixed(1)} MB</span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
