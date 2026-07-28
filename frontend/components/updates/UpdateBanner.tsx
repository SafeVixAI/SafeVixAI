'use client';

// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

import React, { useCallback, useEffect, useRef, useState } from 'react';
import { Download, Shield, X, ArrowUp, RotateCcw, AlertTriangle, CheckCircle, FileText } from 'lucide-react';
import { useShallow } from 'zustand/react/shallow';
import { useAppStore, useUpdateBannerDismissed, useUpdateInfo } from '@/lib/store';
import { checkForUpdates, retryOperation, restartApplication, subscribeToDownloadProgress, verifyReleaseIntegrity } from '@/lib/api/update-api';
import { logClientError } from '@/lib/client-logger';
import ReleaseNotesModal from './ReleaseNotesModal';

export default function UpdateBanner() {
  const updateInfo = useUpdateInfo();
  const dismissed = useUpdateBannerDismissed();
  const { setUpdateInfo, dismissUpdateBanner, setUpdateStatus, setDownloadProgress, incrementRetry } = useAppStore(
    useShallow((s) => ({
      setUpdateInfo: s.setUpdateInfo,
      dismissUpdateBanner: s.dismissUpdateBanner,
      setUpdateStatus: s.setUpdateStatus,
      setDownloadProgress: s.setDownloadProgress,
      incrementRetry: s.incrementRetry,
    }))
  );
  const [checking, setChecking] = useState(false);
  const [showNotes, setShowNotes] = useState(false);
  const cleanupRef = useRef<(() => void) | null>(null);
  const handleRetryRef = useRef<() => void>(() => {});

  useEffect(() => {
    return () => {
      if (cleanupRef.current) cleanupRef.current();
    };
  }, []);

  useEffect(() => {
    const handleOnline = () => {
      if (updateInfo.status === 'error' && updateInfo.latestVersion) {
        incrementRetry();
        handleRetryRef.current();
      }
    };
    window.addEventListener('online', handleOnline);
    return () => window.removeEventListener('online', handleOnline);
  }, [updateInfo.status, updateInfo.latestVersion, incrementRetry]);

  useEffect(() => {
    const check = async () => {
      setChecking(true);
      try {
        const result = await checkForUpdates(updateInfo.channel);
        setUpdateInfo({
          latestVersion: result.latest_version,
          updateAvailable: result.update_available,
          isMandatory: result.is_mandatory,
          isSecurity: result.is_security,
          lastCheckedAt: result.last_checked_at,
          status: result.update_available ? 'available' : 'up-to-date',
        });
      } catch (err) {
        logClientError('UpdateBanner check failed', err);
      } finally {
        setChecking(false);
      }
    };
    if (!dismissed && !checking && !updateInfo.lastCheckedAt) {
      check();
    }
  }, [dismissed]);

  const handleUpdateNow = useCallback(() => {
    setUpdateStatus('downloading');
    if (updateInfo.latestVersion) {
      cleanupRef.current?.();
      cleanupRef.current = subscribeToDownloadProgress(
        updateInfo.latestVersion,
        async (event) => {
          setDownloadProgress(event.percentage);
          if (event.status === 'complete') {
            setUpdateStatus('installing');
            try {
              await verifyReleaseIntegrity(updateInfo.latestVersion!, '/tmp/downloaded');
              setUpdateStatus('installing');
              setTimeout(() => setUpdateStatus('installed'), 1000);
            } catch {
              setUpdateStatus('error');
            }
          }
        },
        () => setUpdateStatus('installed')
      );
    }
  }, [updateInfo.latestVersion, setUpdateStatus, setDownloadProgress]);

  const handleRetry = useCallback(async () => {
    if (updateInfo.latestVersion) {
      await retryOperation('download', updateInfo.latestVersion);
      handleUpdateNow();
    }
  }, [updateInfo.latestVersion, handleUpdateNow]);

  handleRetryRef.current = handleRetry;

  const handleRestart = useCallback(async () => {
    try {
      await restartApplication();
    } catch (err) {
      logClientError('Restart failed', err);
    }
  }, []);

  if (dismissed || (!updateInfo.updateAvailable && updateInfo.status !== 'up-to-date')) return null;

  const isProcessing = updateInfo.status === 'downloading' || updateInfo.status === 'installing';

  const securityBadge = updateInfo.isSecurity ? (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-red-900/40 text-red-300 text-xs font-semibold rounded-full border border-red-700/40">
      <Shield className="w-3 h-3" />
      Security
    </span>
  ) : null;

  return (
    <>
    <div
      role="alert"
      className={`relative w-full px-4 py-3 flex items-center justify-between gap-4 text-sm
        ${updateInfo.isMandatory
          ? 'bg-red-900/30 border-b border-red-700/40 text-red-200'
          : updateInfo.isSecurity
            ? 'bg-amber-900/30 border-b border-amber-700/40 text-amber-200'
            : 'bg-blue-900/30 border-b border-blue-700/40 text-blue-200'
        }`}
    >
      <div className="flex items-center gap-3 flex-1 min-w-0">
        <ArrowUp className="w-4 h-4 shrink-0" />
        <span className="truncate">
          {isProcessing ? (
            <strong>{updateInfo.status === 'downloading' ? `Downloading... ${Math.round(updateInfo.downloadProgress)}%` : 'Installing...'}</strong>
          ) : updateInfo.status === 'installed' ? (
            <strong>Installed! Restart to apply</strong>
          ) : updateInfo.status === 'error' ? (
            <strong className="text-red-300">Update check failed</strong>
          ) : (
            <>
              <strong>Update available:</strong> v{updateInfo.latestVersion}
              <Shield className="w-3 h-3 ml-1 inline text-emerald-400" />
              <span className="text-emerald-400/60 text-xs">Verified</span>
              {updateInfo.currentVersion && (
                <span className="opacity-70"> (current: v{updateInfo.currentVersion})</span>
              )}
            </>
          )}
        </span>
        {!isProcessing && updateInfo.status !== 'installed' && securityBadge}
      </div>

      {/* Progress bar */}
      {updateInfo.status === 'downloading' && (
        <div className="absolute bottom-0 left-0 right-0 h-1 bg-white/10">
          <div
            className="h-full bg-blue-500 transition-all duration-300"
            style={{ width: `${Math.min(updateInfo.downloadProgress, 100)}%` }}
          />
        </div>
      )}

      <div className="flex items-center gap-2 shrink-0">
        {updateInfo.status === 'available' && (
          <>
            <button
              onClick={function () { setShowNotes(true); }}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-slate-700/60 hover:bg-slate-600/60 text-slate-300 text-xs font-medium rounded-lg transition-colors"
              title="View release notes"
            >
              <FileText className="w-3.5 h-3.5" />
              Release Notes
            </button>
            <button
              onClick={handleUpdateNow}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white text-xs font-medium rounded-lg transition-colors"
            >
              <Download className="w-3.5 h-3.5" />
              Update Now
            </button>
          </>
        )}
        {updateInfo.status === 'installed' && (
          <button
            onClick={handleRestart}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-medium rounded-lg transition-colors"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            Restart
          </button>
        )}
        {updateInfo.status === 'error' && (
          <button
            onClick={handleRetry}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-red-600 hover:bg-red-500 text-white text-xs font-medium rounded-lg transition-colors"
          >
            <AlertTriangle className="w-3.5 h-3.5" />
            Retry
          </button>
        )}
        {!updateInfo.isMandatory && !isProcessing && updateInfo.status !== 'installed' && (
          <button
            onClick={dismissUpdateBanner}
            className="p-1.5 hover:bg-white/10 rounded-lg transition-colors"
            aria-label="Dismiss update banner"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>
    </div>
    {showNotes && (
      <ReleaseNotesModal
        version={updateInfo.latestVersion}
        onClose={function () { setShowNotes(false); }}
      />
    )}
    </>
  );
}
