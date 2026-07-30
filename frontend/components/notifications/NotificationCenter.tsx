'use client';

// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  AlertTriangle,
  Bell,
  BellOff,
  Brain,
  CheckCheck,
  ChevronDown,
  Clock,
  Filter,
  Loader2,
  RefreshCw,
  Settings,
  Trash2,
  X,
} from 'lucide-react';

import { useNotificationStore } from '@/lib/store/notification-slice';
import {
  type Notification,
  type NotificationCategory,
  type NotificationChannel,
  type NotificationPriority,
  type NotificationStatus,
  fetchNotifications,
  fetchNotificationStats,
  getNotificationColor,
  getNotificationIcon,
  getTimeAgo,
  markAllNotificationsRead,
  markNotificationRead,
  deleteNotification as apiDeleteNotification,
} from '@/lib/notifications';
import { useAppStore } from '@/lib/store';
import { useNotificationWebSocket } from '@/lib/notifications';

interface NotificationCenterProps {
  onClose?: () => void;
}

const CATEGORY_LABELS: Record<string, string> = {
  system_health: 'System Health',
  ai: 'AI',
  security: 'Security',
  performance: 'Performance',
  update: 'Update',
  maintenance: 'Maintenance',
  incident: 'Incident',
  deployment: 'Deployment',
  usage: 'Usage',
  billing: 'Billing',
  issue: 'Issue',
  sos: 'SOS',
  emergency: 'Emergency',
  challan: 'Challan',
  general: 'General',
};

export function NotificationCenter({ onClose }: NotificationCenterProps) {
  const userId = useAppStore((s) => s.operatorName) || 'anonymous';
  const {
    items,
    unreadCount,
    setItems,
    setUnreadCount,
    addItem,
    removeItem,
    markAsRead,
    markAllAsRead,
  } = useNotificationStore();

  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState<{ total: number; by_category: Record<string, number> } | null>(null);
  const [filterCategory, setFilterCategory] = useState<string | null>(null);
  const [filterStatus, setFilterStatus] = useState<string | null>(null);
  const [showFilters, setShowFilters] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const ws = useNotificationWebSocket(userId);

  useEffect(() => {
    if (ws.notifications.length > 0) {
      const latest = ws.notifications[0];
      addItem(latest);
      setUnreadCount(unreadCount + 1);
    }
  }, [ws.notifications.length]);

  const loadNotifications = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchNotifications(userId, {
        ...(filterCategory ? { category: filterCategory as NotificationCategory } : {}),
        ...(filterStatus === 'unread' ? { status: 'sent' as NotificationStatus } : {}),
      });
      setItems(result.notifications || []);
      setUnreadCount(result.unread || 0);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load notifications');
    } finally {
      setLoading(false);
    }
  }, [userId, filterCategory, filterStatus, setItems, setUnreadCount]);

  const loadStats = useCallback(async () => {
    try {
      const s = await fetchNotificationStats(userId);
      setStats(s);
    } catch {
      // stats are non-critical
    }
  }, [userId]);

  useEffect(() => {
    loadNotifications();
    loadStats();
  }, [loadNotifications, loadStats]);

  const handleMarkRead = async (id: string) => {
    await markNotificationRead(id, userId);
    markAsRead(id);
    setUnreadCount(Math.max(0, unreadCount - 1));
  };

  const handleMarkAllRead = async () => {
    const count = await markAllNotificationsRead(userId);
    markAllAsRead();
    setUnreadCount(0);
  };

  const handleDelete = async (id: string) => {
    await apiDeleteNotification(id);
    removeItem(id);
  };

  const filteredItems = useMemo(() => {
    let result = items;
    if (filterCategory) {
      result = result.filter((n) => n.category === filterCategory);
    }
    if (filterStatus === 'unread') {
      result = result.filter((n) => n.status === 'sent' || n.status === 'delivered');
    }
    return result;
  }, [items, filterCategory, filterStatus]);

  const categoryCounts = useMemo(() => {
    const counts: Record<string, number> = {};
    for (const n of items) {
      const cat = n.category || 'general';
      counts[cat] = (counts[cat] || 0) + 1;
    }
    return counts;
  }, [items]);

  return (
    <div
      className="flex h-full flex-col bg-gray-950 text-gray-100"
      role="region"
      aria-label="Notification center"
      aria-live="polite"
      aria-atomic="false"
    >
      {/* Screen-reader only unread count */}
      <div className="sr-only" role="status" aria-live="polite">
        {unreadCount > 0
          ? `${unreadCount} unread notification${unreadCount !== 1 ? 's' : ''}`
          : 'No unread notifications'}
      </div>

      {/* Header */}
      <div className="flex items-center justify-between border-b border-gray-800 px-4 py-3">
        <div className="flex items-center gap-2">
          <Bell className="h-5 w-5 text-blue-400" aria-hidden="true" />
          <h2 className="text-lg font-semibold" id="notification-center-title">Notifications</h2>
          {unreadCount > 0 && (
            <span className="flex h-5 min-w-5 items-center justify-center rounded-full bg-blue-500 px-1.5 text-xs font-bold text-white">
              {unreadCount}
            </span>
          )}
        </div>
        <div className="flex items-center gap-1">
          <button
            onClick={() => setShowFilters(!showFilters)}
            className="rounded-lg p-1.5 text-gray-400 hover:bg-gray-800 hover:text-gray-200"
            title="Filters"
          >
            <Filter className="h-4 w-4" />
          </button>
          {onClose && (
            <button
              onClick={onClose}
              className="rounded-lg p-1.5 text-gray-400 hover:bg-gray-800 hover:text-gray-200"
            >
              <X className="h-4 w-4" />
            </button>
          )}
        </div>
      </div>

      {/* Filters */}
      {showFilters && (
        <div className="border-b border-gray-800 bg-gray-900/50 px-4 py-2" role="group" aria-label="Filter notifications">
          <div className="mb-2 flex flex-wrap gap-2" role="tablist" aria-label="Category filters">
            <button
              onClick={() => setFilterCategory(null)}
              className={`rounded-full px-3 py-1 text-xs ${
                !filterCategory ? 'bg-blue-500/20 text-blue-400' : 'bg-gray-800 text-gray-400'
              }`}
              role="tab"
              aria-selected={!filterCategory}
              aria-label="Show all categories"
            >
              All
            </button>
            {Object.entries(CATEGORY_LABELS).map(([key, label]) => (
              <button
                key={key}
                onClick={() => setFilterCategory(filterCategory === key ? null : key)}
                className={`rounded-full px-3 py-1 text-xs ${
                  filterCategory === key
                    ? 'bg-blue-500/20 text-blue-400'
                    : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
                }`}
                role="tab"
                aria-selected={filterCategory === key}
                aria-label={`Filter by ${label}`}
              >
                {label}
              </button>
            ))}
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => setFilterStatus(filterStatus === 'unread' ? null : 'unread')}
              className={`rounded-full px-3 py-1 text-xs ${
                filterStatus === 'unread'
                  ? 'bg-blue-500/20 text-blue-400'
                  : 'bg-gray-800 text-gray-400'
              }`}
              aria-pressed={filterStatus === 'unread'}
              aria-label="Toggle unread filter"
            >
              Unread only
            </button>
          </div>
        </div>
      )}

      {/* Actions bar */}
      {unreadCount > 0 && (
        <div className="flex items-center justify-between border-b border-gray-800 px-4 py-2">
          <span className="text-xs text-gray-500">{unreadCount} unread</span>
          <div className="flex gap-2">
            <button
              onClick={handleMarkAllRead}
              className="flex items-center gap-1 rounded px-2 py-1 text-xs text-blue-400 hover:bg-blue-500/10"
            >
              <CheckCheck className="h-3.5 w-3.5" />
              Mark all read
            </button>
            <button
              onClick={loadNotifications}
              className="flex items-center gap-1 rounded px-2 py-1 text-xs text-gray-400 hover:bg-gray-800"
            >
              <RefreshCw className="h-3.5 w-3.5" />
              Refresh
            </button>
          </div>
        </div>
      )}

      {/* Stats summary */}
      {stats && !loading && items.length > 0 && (
        <div className="flex gap-3 border-b border-gray-800 px-4 py-2 text-xs text-gray-500">
          <span>{stats.total} total (7d)</span>
          {Object.entries(stats.by_category).slice(0, 3).map(([cat, count]) => (
            <span key={cat}>{CATEGORY_LABELS[cat] || cat}: {count}</span>
          ))}
        </div>
      )}

      {/* Scrollable list */}
      <div className="flex-1 overflow-y-auto">
        {loading && (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-6 w-6 animate-spin text-gray-500" />
          </div>
        )}

        {error && (
          <div className="mx-4 mt-4 flex items-center gap-2 rounded-lg border border-red-500/20 bg-red-500/10 px-4 py-3 text-sm text-red-400">
            <AlertTriangle className="h-4 w-4 shrink-0" />
            {error}
          </div>
        )}

        {!loading && !error && filteredItems.length === 0 && (
          <div className="flex flex-col items-center justify-center py-16 text-gray-500">
            <BellOff className="mb-3 h-10 w-10" />
            <p className="text-sm">No notifications</p>
            <p className="text-xs text-gray-600">
              {filterCategory ? 'Try a different filter' : 'You\'re all caught up'}
            </p>
          </div>
        )}

        {!loading && filteredItems.map((notification) => (
          <NotificationItem
            key={notification.id}
            notification={notification}
            onMarkRead={handleMarkRead}
            onDelete={handleDelete}
          />
        ))}
      </div>
    </div>
  );
}

// ── Notification Item ──────────────────────────────────────────────────────

interface NotificationItemProps {
  notification: Notification;
  onMarkRead: (id: string) => void;
  onDelete: (id: string) => void;
}

function NotificationItem({ notification, onMarkRead, onDelete }: NotificationItemProps) {
  const [expanded, setExpanded] = useState(false);
  const isUnread = notification.status === 'sent' || notification.status === 'delivered';
  const colorClass = getNotificationColor(notification.priority);

  const itemId = `notification-${notification.id}`;

  return (
    <div
      className={`group border-b border-gray-800/50 transition-colors hover:bg-gray-900/50 ${
        isUnread ? 'border-l-2 border-l-blue-500 bg-blue-500/5' : 'border-l-2 border-l-transparent'
      }`}
      role="listitem"
      aria-labelledby={`${itemId}-title`}
      aria-describedby={notification.body ? `${itemId}-body` : undefined}
    >
      <button
        onClick={() => {
          if (isUnread) onMarkRead(notification.id);
          setExpanded(!expanded);
        }}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            if (isUnread) onMarkRead(notification.id);
            setExpanded(!expanded);
          }
        }}
        className="flex w-full items-start gap-3 px-4 py-3 text-left"
        aria-expanded={expanded}
        aria-label={`${notification.title}${isUnread ? ' (unread)' : ''}`}
      >
        <div className={`mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg ${colorClass}`} aria-hidden="true">
          <span className="text-lg">{/* icon placeholder */}</span>
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex items-start justify-between gap-2">
            <p
              id={`${itemId}-title`}
              className={`text-sm ${isUnread ? 'font-semibold text-gray-100' : 'font-medium text-gray-300'}`}
            >
              {notification.title}
            </p>
            <span className="shrink-0 whitespace-nowrap text-xs text-gray-500">
              {getTimeAgo(notification.created_at)}
            </span>
          </div>
          {notification.body && (
            <p
              id={`${itemId}-body`}
              className={`mt-1 text-xs leading-relaxed ${
                expanded ? '' : 'line-clamp-2'
              } text-gray-400`}
            >
              {notification.body}
            </p>
          )}
          <div className="mt-1.5 flex items-center gap-2">
            {notification.category && (
              <span className="rounded-full bg-gray-800 px-2 py-0.5 text-[10px] text-gray-500">
                {CATEGORY_LABELS[notification.category] || notification.category}
              </span>
            )}
            <span className="text-[10px] text-gray-600">{notification.channel}</span>
            {notification.priority === 'critical' && (
              <span className="flex items-center gap-1 text-[10px] text-red-400">
                <AlertTriangle className="h-3 w-3" aria-hidden="true" />
                Critical
              </span>
            )}
          </div>
        </div>
      </button>

      {/* Actions — always reachable via keyboard */}
      <div className="flex justify-end gap-1 px-4 pb-2 opacity-0 group-hover:opacity-100 focus-within:opacity-100">
        {isUnread && (
          <button
            onClick={() => onMarkRead(notification.id)}
            className="rounded px-2 py-1 text-xs text-blue-400 hover:bg-blue-500/10"
            aria-label={`Mark "${notification.title}" as read`}
          >
            Mark read
          </button>
        )}
        <button
          onClick={() => onDelete(notification.id)}
          className="rounded px-2 py-1 text-xs text-red-400 hover:bg-red-500/10"
          aria-label={`Delete "${notification.title}"`}
        >
          <Trash2 className="h-3 w-3" aria-hidden="true" />
        </button>
      </div>
    </div>
  );
}
