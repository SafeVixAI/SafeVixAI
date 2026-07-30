'use client';

// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

import { useCallback, useEffect, useState } from 'react';
import {
  Bell,
  BellOff,
  Clock,
  Globe,
  Loader2,
  Mail,
  MessageSquare,
  Moon,
  Save,
  Send,
  Settings,
  Shield,
  Smartphone,
  Webhook,
  X,
} from 'lucide-react';

import { useAppStore } from '@/lib/store';
import {
  type NotificationChannel,
  type NotificationPreferenceData,
  fetchPreferences,
  updatePreferences,
} from '@/lib/notifications';

interface NotificationPreferencesPanelProps {
  onClose?: () => void;
}

const CHANNEL_ICONS: Record<string, React.ReactNode> = {
  in_app: <Bell className="h-4 w-4" />,
  email: <Mail className="h-4 w-4" />,
  sms: <MessageSquare className="h-4 w-4" />,
  push: <Smartphone className="h-4 w-4" />,
  slack: <Send className="h-4 w-4" />,
  discord: <Send className="h-4 w-4" />,
  teams: <Send className="h-4 w-4" />,
  webhook: <Webhook className="h-4 w-4" />,
};

const CHANNEL_LABELS: Record<string, string> = {
  in_app: 'In-App',
  email: 'Email',
  sms: 'SMS',
  push: 'Push',
  slack: 'Slack',
  discord: 'Discord',
  teams: 'Microsoft Teams',
  webhook: 'Webhook',
};

const CATEGORY_LABELS: Record<string, string> = {
  system_health: 'System Health',
  ai: 'AI Alerts',
  security: 'Security',
  performance: 'Performance',
  update: 'Updates',
  maintenance: 'Maintenance',
  incident: 'Incidents',
  deployment: 'Deployments',
  usage: 'Usage',
  billing: 'Billing',
  issue: 'Issues',
  sos: 'SOS',
  emergency: 'Emergency',
  challan: 'Challan',
  general: 'General',
};

export function NotificationPreferencesPanel({ onClose }: NotificationPreferencesPanelProps) {
  const userId = useAppStore((s) => s.operatorName) || 'anonymous';
  const [prefs, setPrefs] = useState<NotificationPreferenceData | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await fetchPreferences(userId);
      setPrefs(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load preferences');
    } finally {
      setLoading(false);
    }
  }, [userId]);

  useEffect(() => {
    load();
  }, [load]);

  const save = useCallback(async () => {
    if (!prefs) return;
    setSaving(true);
    setSaved(false);
    try {
      const updated = await updatePreferences(userId, {
        channels_enabled: prefs.channels_enabled,
        categories_enabled: prefs.categories_enabled,
        digest_enabled: prefs.digest_enabled,
        digest_frequency: prefs.digest_frequency,
        dnd_enabled: prefs.dnd_enabled,
        dnd_start_hour: prefs.dnd_start_hour,
        dnd_end_hour: prefs.dnd_end_hour,
        quiet_hours_enabled: prefs.quiet_hours_enabled,
        quiet_hours_start: prefs.quiet_hours_start,
        quiet_hours_end: prefs.quiet_hours_end,
        email_address: prefs.email_address,
        phone_number: prefs.phone_number,
        locale: prefs.locale,
      });
      setPrefs(updated);
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save');
    } finally {
      setSaving(false);
    }
  }, [prefs, userId]);

  const toggleChannel = (channel: string) => {
    if (!prefs) return;
    setPrefs({
      ...prefs,
      channels_enabled: {
        ...prefs.channels_enabled,
        [channel]: !prefs.channels_enabled[channel as NotificationChannel],
      },
    });
  };

  const toggleCategory = (category: string) => {
    if (!prefs) return;
    setPrefs({
      ...prefs,
      categories_enabled: {
        ...prefs.categories_enabled,
        [category]: !prefs.categories_enabled[category as keyof typeof prefs.categories_enabled],
      },
    });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-16">
        <Loader2 className="h-6 w-6 animate-spin text-gray-500" />
      </div>
    );
  }

  if (!prefs) {
    return (
      <div className="p-4 text-center text-sm text-red-400">
        Failed to load preferences: {error}
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col bg-gray-950 text-gray-100">
      <div className="flex items-center justify-between border-b border-gray-800 px-4 py-3">
        <div className="flex items-center gap-2">
          <Settings className="h-5 w-5 text-gray-400" />
          <h2 className="text-lg font-semibold">Notification Preferences</h2>
        </div>
        {onClose && (
          <button onClick={onClose} className="rounded-lg p-1.5 text-gray-400 hover:bg-gray-800">
            <X className="h-4 w-4" />
          </button>
        )}
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-6">
        {/* Channels */}
        <section>
          <h3 className="mb-3 text-sm font-medium text-gray-300">Channels</h3>
          <div className="grid grid-cols-2 gap-2">
            {Object.entries(CHANNEL_LABELS).map(([key, label]) => (
              <button
                key={key}
                onClick={() => toggleChannel(key)}
                className={`flex items-center gap-2 rounded-lg border px-3 py-2.5 text-sm transition-colors ${
                  prefs.channels_enabled[key as NotificationChannel]
                    ? 'border-blue-500/30 bg-blue-500/10 text-blue-400'
                    : 'border-gray-800 bg-gray-900 text-gray-500 hover:border-gray-700'
                }`}
              >
                {CHANNEL_ICONS[key]}
                {label}
              </button>
            ))}
          </div>
        </section>

        {/* Categories */}
        <section>
          <h3 className="mb-3 text-sm font-medium text-gray-300">Categories</h3>
          <div className="grid grid-cols-2 gap-2">
            {Object.entries(CATEGORY_LABELS).map(([key, label]) => (
              <button
                key={key}
                onClick={() => toggleCategory(key)}
                className={`rounded-lg border px-3 py-2 text-left text-sm transition-colors ${
                  prefs.categories_enabled[key as keyof typeof prefs.categories_enabled]
                    ? 'border-blue-500/30 bg-blue-500/10 text-blue-400'
                    : 'border-gray-800 bg-gray-900 text-gray-500 hover:border-gray-700'
                }`}
              >
                {label}
              </button>
            ))}
          </div>
        </section>

        {/* DND */}
        <section>
          <h3 className="mb-3 flex items-center gap-2 text-sm font-medium text-gray-300">
            <Moon className="h-4 w-4" /> Do Not Disturb
          </h3>
          <label className="flex items-center gap-3 rounded-lg border border-gray-800 bg-gray-900 p-3">
            <input
              type="checkbox"
              checked={prefs.dnd_enabled}
              onChange={() => setPrefs({ ...prefs, dnd_enabled: !prefs.dnd_enabled })}
              className="h-4 w-4 rounded border-gray-600 bg-gray-800 text-blue-500"
            />
            <div>
              <p className="text-sm text-gray-300">Enable DND</p>
              <p className="text-xs text-gray-500">Suppress non-critical notifications</p>
            </div>
          </label>
          {prefs.dnd_enabled && (
            <div className="mt-2 flex items-center gap-2">
              <input
                type="number"
                min={0}
                max={23}
                value={prefs.dnd_start_hour ?? 22}
                onChange={(e) => setPrefs({ ...prefs, dnd_start_hour: parseInt(e.target.value) })}
                className="w-16 rounded border border-gray-800 bg-gray-900 px-2 py-1 text-center text-sm text-gray-300"
              />
              <span className="text-gray-500">:00 to</span>
              <input
                type="number"
                min={0}
                max={23}
                value={prefs.dnd_end_hour ?? 7}
                onChange={(e) => setPrefs({ ...prefs, dnd_end_hour: parseInt(e.target.value) })}
                className="w-16 rounded border border-gray-800 bg-gray-900 px-2 py-1 text-center text-sm text-gray-300"
              />
              <span className="text-gray-500">:00</span>
            </div>
          )}
        </section>

        {/* Digest */}
        <section>
          <h3 className="mb-3 flex items-center gap-2 text-sm font-medium text-gray-300">
            <Clock className="h-4 w-4" /> Digest Mode
          </h3>
          <label className="flex items-center gap-3 rounded-lg border border-gray-800 bg-gray-900 p-3">
            <input
              type="checkbox"
              checked={prefs.digest_enabled}
              onChange={() => setPrefs({ ...prefs, digest_enabled: !prefs.digest_enabled })}
              className="h-4 w-4 rounded border-gray-600 bg-gray-800 text-blue-500"
            />
            <div>
              <p className="text-sm text-gray-300">Enable Digest</p>
              <p className="text-xs text-gray-500">Batch notifications into periodic summaries</p>
            </div>
          </label>
          {prefs.digest_enabled && (
            <select
              value={prefs.digest_frequency}
              onChange={(e) => setPrefs({ ...prefs, digest_frequency: e.target.value as 'hourly' | 'daily' | 'weekly' })}
              className="mt-2 w-full rounded border border-gray-800 bg-gray-900 px-3 py-2 text-sm text-gray-300"
            >
              <option value="hourly">Hourly</option>
              <option value="daily">Daily</option>
              <option value="weekly">Weekly</option>
            </select>
          )}
        </section>

        {/* Contact Info */}
        <section>
          <h3 className="mb-3 flex items-center gap-2 text-sm font-medium text-gray-300">
            <Mail className="h-4 w-4" /> Contact Information
          </h3>
          <div className="space-y-2">
            <input
              type="email"
              placeholder="Email address"
              value={prefs.email_address || ''}
              onChange={(e) => setPrefs({ ...prefs, email_address: e.target.value })}
              className="w-full rounded border border-gray-800 bg-gray-900 px-3 py-2 text-sm text-gray-300 placeholder-gray-600"
            />
            <input
              type="tel"
              placeholder="Phone number"
              value={prefs.phone_number || ''}
              onChange={(e) => setPrefs({ ...prefs, phone_number: e.target.value })}
              className="w-full rounded border border-gray-800 bg-gray-900 px-3 py-2 text-sm text-gray-300 placeholder-gray-600"
            />
          </div>
        </section>

        {/* Locale */}
        <section>
          <h3 className="mb-3 flex items-center gap-2 text-sm font-medium text-gray-300">
            <Globe className="h-4 w-4" /> Locale
          </h3>
          <select
            value={prefs.locale}
            onChange={(e) => setPrefs({ ...prefs, locale: e.target.value })}
            className="w-full rounded border border-gray-800 bg-gray-900 px-3 py-2 text-sm text-gray-300"
          >
            <option value="en">English</option>
            <option value="hi">Hindi</option>
            <option value="ta">Tamil</option>
            <option value="te">Telugu</option>
            <option value="bn">Bengali</option>
            <option value="mr">Marathi</option>
            <option value="gu">Gujarati</option>
            <option value="kn">Kannada</option>
            <option value="ml">Malayalam</option>
            <option value="pa">Punjabi</option>
          </select>
        </section>

        {error && (
          <div className="rounded-lg border border-red-500/20 bg-red-500/10 px-4 py-2 text-sm text-red-400">
            {error}
          </div>
        )}
      </div>

      {/* Save footer */}
      <div className="border-t border-gray-800 px-4 py-3">
        <button
          onClick={save}
          disabled={saving}
          className="flex w-full items-center justify-center gap-2 rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-medium text-white transition-colors hover:bg-blue-700 disabled:opacity-50"
        >
          {saving ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Save className="h-4 w-4" />
          )}
          {saving ? 'Saving...' : saved ? 'Saved!' : 'Save Preferences'}
        </button>
      </div>
    </div>
  );
}
