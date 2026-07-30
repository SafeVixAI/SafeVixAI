// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

'use client';

import React, { useEffect, useState } from 'react';
import { fetchRelease } from '@/lib/api/update-api';
import ReleaseNotesViewer from './ReleaseNotesViewer';
import type { ReleaseDetail } from '@/lib/api/update-api';

interface ReleaseNotesModalProps {
  version: string | null;
  onClose: () => void;
}

export default function ReleaseNotesModal({ version, onClose }: ReleaseNotesModalProps) {
  const [release, setRelease] = useState<ReleaseDetail | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(function () {
    if (!version) return;
    setLoading(true);
    fetchRelease(version)
      .then(function (data) { setRelease(data); })
      .catch(function () { setRelease(null); })
      .finally(function () { setLoading(false); });
  }, [version]);

  if (!version) return null;

  if (loading) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
        <div className="p-6 bg-slate-900 border border-slate-700/40 rounded-xl">
          <p className="text-slate-400">Loading release notes...</p>
        </div>
      </div>
    );
  }

  return <ReleaseNotesViewer release={release} onClose={onClose} />;
}
