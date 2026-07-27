'use client';

// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

import React, { useCallback, useEffect, useRef, useState } from 'react';
import { ArrowUp, CheckCircle, Clock, Download, RefreshCw, RotateCcw, AlertTriangle } from 'lucide-react';
import { useAppStore, useUpdateInfo } from '@/lib/store';
import { useShallow } from 'zustand/react/shallow';
import { restartApplication, subscribeToDownloadProgress } from '@/lib/api/update-api';
import { logClientError } from '@/lib/client-logger';

export default function UpdateWidget() {
  const updateInfo = useUpdateInfo();
  const { setUpdateInfo, setUpdateStatus, setDownloadProgress } = useAppStore(
    useShallow((s) => ({
      setUpdateInfo: s.setUpdateInfo,
      setUpdateStatus: s.setUpdateStatus,
      setDownloadProgress: s.setDownloadProgress,
    }))
  );
  const [restarting, setRestarting] = useState(false);
  const cleanupRef = useRef<(() => void) | null>(null);

  useEffect(() => {
    return () => {
      if (cleanupRef.current) cleanupRef.current();
    };
  }, []);

  const handleCheckNow = useCallback(async () => {
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
  }, [updateInfo.channel, setUpdateInfo]);

  const handleUpdateNow = useCallback(() => {
    setUpdateStatus('downloading');
    if (updateInfo.latestVersion) {
      cleanupRef.current?.();
      cleanupRef.current = subscribeToDownloadProgress(
        updateInfo.latestVersion,
        (event) => {
          setDownloadProgress(event.percentage);
          if (event.status === 'complete') {
            setUpdateStatus('installing');
            setTimeout(() => setUpdateStatus('installed'), 1000);
          }
        },
        () => setUpdateStatus('installed')
      );
    }
  }, [updateInfo.latestVersion, setUpdateStatus, setDownloadProgress]);

  const handleRestart = useCallback(async () => {
    setRestarting(true);
    try {
      await restartApplication();
    } catch (err) {
      logClientError('Restart failed', err);
    } finally {
      setRestarting(false);
    }
  }, []);

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
          updateInfo.status === 'downloading' ? 'bg-blue-400 animate-pulse' :
          updateInfo.status === 'installing' ? 'bg-purple-400 animate-pulse' :
          updateInfo.status === 'installed' ? 'bg-emerald-400' :
          updateInfo.status === 'error' ? 'bg-red-400' :
          'bg-blue-400 animate-pulse'
        }`} />
        <span className="text-xs text-white/70">
          {updateInfo.status === 'up-to-date' && 'Up to date'}
          {updateInfo.status === 'available' && `v${updateInfo.latestVersion} available`}
          {updateInfo.status === 'downloading' && `Downloading... ${Math.round(updateInfo.downloadProgress)}%`}
          {updateInfo.status === 'installing' && 'Installing...'}
          {updateInfo.status === 'installed' && 'Installed! Restart to apply'}
          {updateInfo.status === 'error' && 'Check failed'}
        </span>
      </div>

      {/* Progress Bar */}
      {(updateInfo.status === 'downloading') && (
        <div className="w-full bg-white/10 rounded-full h-1.5 overflow-hidden">
          <div
            className="h-full bg-blue-500 rounded-full transition-all duration-300"
            style={{ width: `${Math.min(updateInfo.downloadProgress, 100)}%` }}
          />
        </div>
      )}

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

      {updateInfo.updateAvailable && updateInfo.status !== 'downloading' && updateInfo.status !== 'installing' && (
        <button
          onClick={handleUpdateNow}
          className="w-full inline-flex items-center justify-center gap-1.5 px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white text-xs font-medium rounded-lg transition-colors"
        >
          <Download className="w-3.5 h-3.5" />
          Update Now
        </button>
      )}

      {(updateInfo.status === 'installed' || updateInfo.status === 'installing') && (
        <button
          onClick={handleRestart}
          disabled={restarting}
          className="w-full inline-flex items-center justify-center gap-1.5 px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white text-xs font-medium rounded-lg transition-colors"
        >
          <RotateCcw className="w-3.5 h-3.5" />
          {restarting ? 'Restarting...' : 'Restart Now'}
        </button>
      )}

      {updateInfo.status === 'error' && (
        <div className="flex items-center gap-1.5 text-xs text-red-400/80">
          <AlertTriangle className="w-3 h-3" />
          <button onClick={handleCheckNow} className="underline hover:text-red-300">Retry</button>
        </div>
      )}
    </div>
  );
}
