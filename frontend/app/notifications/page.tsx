'use client';

// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

import { Bell, Settings } from 'lucide-react';
import { useNotificationStore } from '@/lib/store/notification-slice';
import { NotificationCenter } from '@/components/notifications/NotificationCenter';
import { NotificationPreferencesPanel } from '@/components/notifications/NotificationPreferencesPanel';

export default function NotificationsPage() {
  const { isCenterOpen, preferencesOpen, setCenterOpen, setPreferencesOpen, unreadCount } =
    useNotificationStore();

  return (
    <div className="mx-auto flex min-h-screen max-w-4xl flex-col bg-gray-950 text-gray-100">
      <div className="flex items-center justify-between border-b border-gray-800 px-6 py-4">
        <div className="flex items-center gap-3">
          <Bell className="h-6 w-6 text-blue-400" />
          <h1 className="text-xl font-bold">Notification Center</h1>
          {unreadCount > 0 && (
            <span className="flex h-6 items-center rounded-full bg-blue-500 px-2.5 text-xs font-bold text-white">
              {unreadCount} unread
            </span>
          )}
        </div>
        <button
          onClick={() => setPreferencesOpen(!preferencesOpen)}
          className="flex items-center gap-2 rounded-lg border border-gray-800 px-3 py-2 text-sm text-gray-400 transition-colors hover:border-gray-700 hover:text-gray-200"
        >
          <Settings className="h-4 w-4" />
          Preferences
        </button>
      </div>

      <div className="flex flex-1">
        <div className="flex-1">
          <NotificationCenter />
        </div>
        {preferencesOpen && (
          <div className="w-full max-w-md border-l border-gray-800">
            <NotificationPreferencesPanel onClose={() => setPreferencesOpen(false)} />
          </div>
        )}
      </div>
    </div>
  );
}
