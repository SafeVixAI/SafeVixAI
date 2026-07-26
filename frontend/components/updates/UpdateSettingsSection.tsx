'use client';

// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

import React, { useEffect, useState } from 'react';
import { ArrowUp, CheckCircle, Clock, Download, RefreshCw, RotateCcw } from 'lucide-react';
import { useAppStore, useUpdateInfo } from '@/lib/store';
import { useShallow } from 'zustand/react/shallow';
import { fetchChannels, fetchUpdateHistory, fetchUpdateSettings, updateUpdateSettings } from '@/lib/api/update-api';
import { logClientError } from '@/lib/client-logger';
import type { ChannelInfo, InstallationRecord, UpdateSettingsResponse } from '@/lib/api/update-api';
import { SettingRow } from '@/components/ui/SettingRow';
import Toggle from '@/components/dashboard/Toggle';
import Toast from '@/components/dashboard/Toast';

export default function UpdateSettingsSection() {
  const updateInfo = useUpdateInfo();
  const { setUpdateInfo, setUpdateStatus } = useAppStore(
    useShallow((s) => ({
      setUpdateInfo: s.setUpdateInfo,
      setUpdateStatus: s.setUpdateStatus,
    }))
  );

  const [settings, setSettings] = useState<UpdateSettingsResponse | null>(null);
  const [channels, setChannels] = useState<ChannelInfo[]>([]);
  const [history, setHistory] = useState<InstallationRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' | 'info' } | null>(null);

  useEffect(() => {
    const load = async () => {
      try {
        const [s, c, h] = await Promise.all([
          fetchUpdateSettings(),
          fetchChannels(),
          fetchUpdateHistory(5),
        ]);
        setSettings(s);
        setChannels(c);
        setHistory(h.installations);
      } catch (err) {
        logClientError('Failed to load update settings', err);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const handleToggle = async (key: string, value: boolean) => {
    if (!settings) return;
    setSaving(true);
    try {
      const updated = await updateUpdateSettings({ [key]: value });
      setSettings(updated);
      setToast({ message: 'Update settings saved', type: 'success' });
    } catch (err) {
      logClientError('Failed to save update settings', err);
      setToast({ message: 'Failed to save settings', type: 'error' });
    } finally {
      setSaving(false);
    }
  };

  const handleChannelChange = async (channel: string) => {
    if (!settings) return;
    setSaving(true);
    try {
      const updated = await updateUpdateSettings({ channel });
      setSettings(updated);
      setUpdateInfo({ channel: channel as any });
      setToast({ message: `Channel changed to ${channel}`, type: 'success' });
    } catch (err) {
      logClientError('Failed to change channel', err);
      setToast({ message: 'Failed to change channel', type: 'error' });
    } finally {
      setSaving(false);
    }
  };

  const handleCheckNow = async () => {
    try {
      const { checkForUpdates: check } = await import('@/lib/api/update-api');
      const result = await check(updateInfo.channel);
      setUpdateInfo({
        latestVersion: result.latest_version,
        updateAvailable: result.update_available,
        isMandatory: result.is_mandatory,
        isSecurity: result.is_security,
        lastCheckedAt: result.last_checked_at,
        status: result.update_available ? 'available' : 'up-to-date',
        currentVersion: result.current_version,
      });
      setToast({
        message: result.update_available ? `Update v${result.latest_version} available` : 'Up to date',
        type: result.update_available ? 'info' : 'success',
      });
    } catch (err) {
      logClientError('Update check failed', err);
      setToast({ message: 'Check failed', type: 'error' });
    }
  };

  if (loading) {
    return (
      <div className="p-4 text-sm text-white/40 animate-pulse">
        Loading update settings...
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          onClose={() => setToast(null)}
        />
      )}

      {/* Channel Selector */}
      <div className="space-y-2">
        <label className="text-xs font-medium text-white/60 uppercase tracking-wider">
          Release Channel
        </label>
        <div className="flex flex-wrap gap-2">
          {channels.map((ch) => (
            <button
              key={ch.channel}
              onClick={() => handleChannelChange(ch.channel)}
              disabled={saving}
              className={`px-3 py-1.5 text-xs font-medium rounded-lg border transition-colors ${
                settings?.channel === ch.channel
                  ? 'bg-blue-600/30 border-blue-500/50 text-blue-300'
                  : 'bg-white/5 border-white/10 text-white/60 hover:bg-white/10'
              }`}
            >
              {ch.display_name}
              {ch.latest_version && (
                <span className="ml-1.5 opacity-70">v{ch.latest_version}</span>
              )}
            </button>
          ))}
        </div>
      </div>

      <SettingRow
        icon={<ArrowUp className="w-4 h-4" />}
        label="Auto-update"
        description="Automatically download and install updates"
        control={
          <Toggle
            enabled={settings?.auto_update_enabled ?? true}
            onChange={(v) => handleToggle('auto_update_enabled', v)}
            disabled={saving}
          />
        }
      />

      <SettingRow
        icon={<Download className="w-4 h-4" />}
        label="Background download"
        description="Download updates in the background"
        control={
          <Toggle
            enabled={settings?.background_download ?? true}
            onChange={(v) => handleToggle('background_download', v)}
            disabled={saving}
          />
        }
      />

      <SettingRow
        icon={<RotateCcw className="w-4 h-4" />}
        label="Auto-restart"
        description="Automatically restart after update"
        control={
          <Toggle
            enabled={settings?.auto_restart ?? false}
            onChange={(v) => handleToggle('auto_restart', v)}
            disabled={saving}
          />
        }
      />

      <SettingRow
        icon={<CheckCircle className="w-4 h-4" />}
        label="Update notifications"
        description="Show notification when updates are available"
        control={
          <Toggle
            enabled={settings?.notify_on_update ?? true}
            onChange={(v) => handleToggle('notify_on_update', v)}
            disabled={saving}
          />
        }
      />

      {/* Version Info */}
      <div className="rounded-lg bg-white/5 p-3 space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-xs text-white/60">Current version</span>
          <span className="text-sm font-mono text-white/90">v{updateInfo.currentVersion}</span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-xs text-white/60">Latest version</span>
          <span className="text-sm font-mono text-white/90">
            {updateInfo.latestVersion ? `v${updateInfo.latestVersion}` : '-'}
          </span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-xs text-white/60">Last checked</span>
          <div className="flex items-center gap-2">
            <span className="text-xs text-white/60">
              {updateInfo.lastCheckedAt
                ? new Date(updateInfo.lastCheckedAt).toLocaleDateString()
                : 'Never'}
            </span>
            <button
              onClick={handleCheckNow}
              className="p-1 hover:bg-white/10 rounded-lg transition-colors"
              aria-label="Check for updates"
            >
              <RefreshCw className="w-3.5 h-3.5 text-white/40" />
            </button>
          </div>
        </div>
      </div>

      {/* Update History */}
      {history.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-xs font-medium text-white/60 uppercase tracking-wider">
            Recent Updates
          </h4>
          <div className="space-y-1">
            {history.map((item) => (
              <div
                key={item.id}
                className="flex items-center justify-between rounded-lg bg-white/5 px-3 py-2"
              >
                <div className="flex items-center gap-2">
                  <span className="text-xs font-mono text-white/80">
                    v{item.release_version}
                  </span>
                  <span className={`text-[10px] px-1.5 py-0.5 rounded-full font-medium ${
                    item.status === 'installed' ? 'bg-emerald-900/40 text-emerald-300' :
                    item.status === 'rolled_back' ? 'bg-amber-900/40 text-amber-300' :
                    item.status === 'failed' ? 'bg-red-900/40 text-red-300' :
                    'bg-blue-900/40 text-blue-300'
                  }`}>
                    {item.status}
                  </span>
                </div>
                <span className="text-[10px] text-white/40">
                  {item.completed_at
                    ? new Date(item.completed_at).toLocaleDateString()
                    : new Date(item.created_at).toLocaleDateString()}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
