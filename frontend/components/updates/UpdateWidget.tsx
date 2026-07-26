'use client';

// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

import React from 'react';
import { ArrowUp, CheckCircle, Clock, Download, RefreshCw } from 'lucide-react';
import { useAppStore, useUpdateInfo } from '@/lib/store';
import { useShallow } from 'zustand/react/shallow';

export default function UpdateWidget() {
  const updateInfo = useUpdateInfo();
  const { setUpdateInfo, setUpdateStatus } = useAppStore(
    useShallow((s) => ({
      setUpdateInfo: s.setUpdateInfo,
      setUpdateStatus: s.setUpdateStatus,
    }))
  );

  const handleCheckNow = async () => {
    setUpdateInfo({ status: 'up-to-date' });
    try {
      const { checkForUpdates } = await import('@/lib/api/update-api');
      const result = await checkForUpdates(updateInfo.channel);
      setUpdateInfo({
        latestVersion: result.latest_version,
        updateAvailable: result.update_available,
        isMandatory: result.is_mandatory,
        isSecurity: result.is_security,
        lastCheckedAt: result.last_checked_at,
        status: result.update_available ? 'available' : 'up-to-date',
        currentVersion: result.current_version,
      });
    } catch {
      setUpdateInfo({ status: 'error' });
    }
  };

  const formatTime = (iso: string | null) => {
    if (!iso) return 'Never';
    try {
      const d = new Date(iso);
      return d.toLocaleDateString(undefined, {
        month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
      });
    } catch {
      return 'Never';
    }
  };

  return (
    <div className="rounded-xl border border-white/10 bg-white/5 p-4 space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-white/90 flex items-center gap-2">
          <ArrowUp className="w-4 h-4 text-emerald-400" />
          Updates
        </h3>
        <button
          onClick={handleCheckNow}
          className="p-1.5 hover:bg-white/10 rounded-lg transition-colors"
          aria-label="Check for updates"
          title="Check for updates"
        >
          <RefreshCw className="w-3.5 h-3.5 text-white/60" />
        </button>
      </div>

      <div className="flex items-center gap-3">
        <div className={`w-2 h-2 rounded-full ${
          updateInfo.status === 'up-to-date' ? 'bg-emerald-400' :
          updateInfo.status === 'available' ? 'bg-amber-400' :
          updateInfo.status === 'error' ? 'bg-red-400' :
          'bg-blue-400 animate-pulse'
        }`} />
        <span className="text-xs text-white/70">
          {updateInfo.status === 'up-to-date' && 'Up to date'}
          {updateInfo.status === 'available' && `v${updateInfo.latestVersion} available`}
          {updateInfo.status === 'downloading' && 'Downloading...'}
          {updateInfo.status === 'installing' && 'Installing...'}
          {updateInfo.status === 'error' && 'Check failed'}
        </span>
      </div>

      <div className="flex items-center gap-2 text-xs text-white/40">
        <Clock className="w-3 h-3" />
        <span>Last checked: {formatTime(updateInfo.lastCheckedAt)}</span>
      </div>

      {updateInfo.status === 'up-to-date' && (
        <div className="flex items-center gap-1.5 text-xs text-emerald-400/80">
          <CheckCircle className="w-3 h-3" />
          v{updateInfo.currentVersion}
        </div>
      )}

      {updateInfo.updateAvailable && (
        <button
          onClick={() => setUpdateStatus('downloading')}
          className="w-full inline-flex items-center justify-center gap-1.5 px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white text-xs font-medium rounded-lg transition-colors"
        >
          <Download className="w-3.5 h-3.5" />
          Update Now
        </button>
      )}
    </div>
  );
}
