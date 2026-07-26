'use client';

// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

import React, { useEffect, useState } from 'react';
import { Download, Shield, X, ArrowUp } from 'lucide-react';
import { useShallow } from 'zustand/react/shallow';
import { useAppStore, useUpdateBannerDismissed, useUpdateInfo } from '@/lib/store';
import { checkForUpdates } from '@/lib/api/update-api';
import { logClientError } from '@/lib/client-logger';

export default function UpdateBanner() {
  const updateInfo = useUpdateInfo();
  const dismissed = useUpdateBannerDismissed();
  const { setUpdateInfo, dismissUpdateBanner, setUpdateStatus } = useAppStore(
    useShallow((s) => ({
      setUpdateInfo: s.setUpdateInfo,
      dismissUpdateBanner: s.dismissUpdateBanner,
      setUpdateStatus: s.setUpdateStatus,
    }))
  );
  const [checking, setChecking] = useState(false);

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

  if (dismissed || !updateInfo.updateAvailable) return null;

  const securityBadge = updateInfo.isSecurity ? (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-red-900/40 text-red-300 text-xs font-semibold rounded-full border border-red-700/40">
      <Shield className="w-3 h-3" />
      Security
    </span>
  ) : null;

  return (
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
          <strong>Update available:</strong> v{updateInfo.latestVersion}
          {updateInfo.currentVersion && (
            <span className="opacity-70"> (current: v{updateInfo.currentVersion})</span>
          )}
        </span>
        {securityBadge}
      </div>
      <div className="flex items-center gap-2 shrink-0">
        <button
          onClick={() => setUpdateStatus('downloading')}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white text-xs font-medium rounded-lg transition-colors"
        >
          <Download className="w-3.5 h-3.5" />
          Update Now
        </button>
        {!updateInfo.isMandatory && (
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
  );
}
