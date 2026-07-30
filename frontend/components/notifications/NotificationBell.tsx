'use client';

// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

import { useEffect, useRef, useState } from 'react';
import { Bell, BellDot, Settings } from 'lucide-react';

import { useNotificationStore } from '@/lib/store/notification-slice';
import { NotificationCenter } from './NotificationCenter';
import { NotificationPreferencesPanel } from './NotificationPreferencesPanel';

interface NotificationBellProps {
  className?: string;
}

export function NotificationBell({ className = '' }: NotificationBellProps) {
  const { unreadCount, isCenterOpen, toggleCenter, setCenterOpen, preferencesOpen, setPreferencesOpen } =
    useNotificationStore();
  const [showDot, setShowDot] = useState(false);
  const prevUnreadRef = useRef(unreadCount);

  useEffect(() => {
    if (unreadCount > prevUnreadRef.current) {
      setShowDot(true);
      const timer = setTimeout(() => setShowDot(false), 5000);
      prevUnreadRef.current = unreadCount;
      return () => clearTimeout(timer);
    }
    prevUnreadRef.current = unreadCount;
  }, [unreadCount]);

  return (
    <>
      <div className={`relative ${className}`}>
        <button
          onClick={toggleCenter}
          className="relative flex h-9 w-9 items-center justify-center rounded-lg text-gray-400 transition-colors hover:bg-gray-800 hover:text-gray-200"
          aria-label={`Notifications${unreadCount > 0 ? ` (${unreadCount} unread)` : ''}`}
        >
          {unreadCount > 0 || showDot ? (
            <BellDot className="h-5 w-5" />
          ) : (
            <Bell className="h-5 w-5" />
          )}
          {unreadCount > 0 && (
            <span className="absolute -right-0.5 -top-0.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-blue-500 px-1 text-[10px] font-bold text-white">
              {unreadCount > 99 ? '99+' : unreadCount}
            </span>
          )}
        </button>
      </div>

      {/* Slide-over panel */}
      {isCenterOpen && (
        <div className="fixed inset-0 z-50 flex">
          <div
            className="flex-1 bg-black/50 backdrop-blur-sm"
            onClick={() => setCenterOpen(false)}
          />
          <div className="flex w-full max-w-md flex-col bg-gray-950 shadow-2xl">
            <NotificationCenter onClose={() => setCenterOpen(false)} />
          </div>
        </div>
      )}

      {preferencesOpen && (
        <div className="fixed inset-0 z-50 flex">
          <div
            className="flex-1 bg-black/50 backdrop-blur-sm"
            onClick={() => setPreferencesOpen(false)}
          />
          <div className="flex w-full max-w-lg flex-col bg-gray-950 shadow-2xl">
            <NotificationPreferencesPanel onClose={() => setPreferencesOpen(false)} />
          </div>
        </div>
      )}
    </>
  );
}
