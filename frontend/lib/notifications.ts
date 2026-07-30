// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

import { useCallback, useEffect, useRef, useState } from 'react';

export type NotificationChannel =
  | 'in_app' | 'desktop' | 'email' | 'sms' | 'push'
  | 'slack' | 'discord' | 'webhook' | 'teams';

export type NotificationPriority =
  | 'low' | 'normal' | 'high' | 'critical';

export type NotificationCategory =
  | 'system_health' | 'ai' | 'security' | 'performance'
  | 'update' | 'maintenance' | 'incident' | 'deployment'
  | 'usage' | 'billing' | 'issue' | 'sos' | 'emergency'
  | 'challan' | 'general';

export type NotificationStatus =
  | 'pending' | 'sent' | 'delivered' | 'read' | 'failed' | 'cancelled';

export interface Notification {
  id: string;
  user_id?: string;
  org_id?: string;
  channel?: NotificationChannel;
  category?: NotificationCategory;
  priority: NotificationPriority;
  status: NotificationStatus;
  title: string;
  body?: string;
  metadata?: Record<string, unknown>;
  source?: string;
  correlation_id?: string;
  read_at?: string;
  delivered_at?: string;
  scheduled_for?: string;
  expires_at?: string;
  created_at: string;
  updated_at?: string;
}

export interface NotificationPreferenceData {
  id: string;
  user_id: string;
  channels_enabled: Record<string, boolean>;
  categories_enabled: Record<string, boolean>;
  digest_enabled: boolean;
  digest_frequency: 'hourly' | 'daily' | 'weekly';
  dnd_enabled: boolean;
  dnd_start_hour?: number;
  dnd_end_hour?: number;
  dnd_timezone: string;
  quiet_hours_enabled: boolean;
  quiet_hours_start?: string;
  quiet_hours_end?: string;
  push_token: boolean;
  slack_webhook_url: boolean;
  discord_webhook_url: boolean;
  teams_webhook_url: boolean;
  webhook_url: boolean;
  email_address?: string;
  phone_number?: string;
  locale: string;
  max_daily_notifications?: number;
}

export interface NotificationStats {
  total: number;
  days: number;
  by_category: Record<string, number>;
  by_channel: Record<string, number>;
}

export interface NotificationListResponse {
  notifications: Notification[];
  total: number;
  unread: number;
  limit: number;
  offset: number;
}

export interface OfflineNotification {
  id: string;
  userId: string;
  notification: {
    channel: NotificationChannel;
    category: NotificationCategory;
    title: string;
    body?: string;
    priority: NotificationPriority;
    metadata?: Record<string, unknown>;
  };
  createdAt: number;
}

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
const API_PREFIX = `${BACKEND_URL}/api/v1/notifications`;

async function apiRequest<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_PREFIX}${path}`;
  const res = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    },
    ...options,
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(`Notification API error ${res.status}: ${err}`);
  }
  return res.json();
}

export async function fetchNotifications(
  userId: string,
  params?: {
    status?: NotificationStatus;
    category?: NotificationCategory;
    channel?: NotificationChannel;
    priority?: NotificationPriority;
    limit?: number;
    offset?: number;
  }
): Promise<NotificationListResponse> {
  const search = new URLSearchParams({ user_id: userId });
  if (params?.status) search.set('status', params.status);
  if (params?.category) search.set('category', params.category);
  if (params?.channel) search.set('channel', params.channel);
  if (params?.priority) search.set('priority', params.priority);
  if (params?.limit) search.set('limit', String(params.limit));
  if (params?.offset) search.set('offset', String(params.offset));
  return apiRequest<NotificationListResponse>(`?${search}`);
}

export async function markNotificationRead(
  notificationId: string,
  userId: string
): Promise<void> {
  await apiRequest(`/${notificationId}/read?user_id=${userId}`, {
    method: 'POST',
  });
}

export async function markAllNotificationsRead(userId: string): Promise<number> {
  const res = await apiRequest<{ count: number }>(
    `/read-all?user_id=${userId}`,
    { method: 'POST' }
  );
  return res.count;
}

export async function deleteNotification(notificationId: string): Promise<void> {
  await apiRequest(`/${notificationId}`, { method: 'DELETE' });
}

export async function fetchPreferences(userId: string): Promise<NotificationPreferenceData> {
  return apiRequest<NotificationPreferenceData>(`/preferences?user_id=${userId}`);
}

export async function updatePreferences(
  userId: string,
  payload: Partial<NotificationPreferenceData>
): Promise<NotificationPreferenceData> {
  return apiRequest<NotificationPreferenceData>(`/preferences?user_id=${userId}`, {
    method: 'PUT',
    body: JSON.stringify(payload),
  });
}

export async function fetchNotificationStats(
  userId: string,
  days = 7
): Promise<NotificationStats> {
  return apiRequest<NotificationStats>(`/stats?user_id=${userId}&days=${days}`);
}

export async function sendNotification(
  userId: string,
  channel: NotificationChannel,
  title: string,
  body?: string,
  opts?: {
    category?: NotificationCategory;
    priority?: NotificationPriority;
    source?: string;
    correlation_id?: string;
  }
): Promise<Notification> {
  const search = new URLSearchParams({
    user_id: userId,
    channel,
    title: title,
  });
  if (body) search.set('body', body);
  if (opts?.category) search.set('category', opts.category);
  if (opts?.priority) search.set('priority', opts.priority);
  if (opts?.source) search.set('source', opts.source);
  if (opts?.correlation_id) search.set('correlation_id', opts.correlation_id);
  return apiRequest<Notification>(`/send?${search}`, { method: 'POST' });
}

// ── Analytics ──────────────────────────────────────────────────────────────

export async function trackNotificationOpen(
  notificationId: string,
  userId: string,
  userAgent?: string
): Promise<void> {
  const search = new URLSearchParams({ user_id: userId });
  if (userAgent) search.set('user_agent', userAgent);
  await apiRequest(`/${notificationId}/open?${search}`, { method: 'POST' });
}

export async function trackNotificationClick(
  notificationId: string,
  userId: string,
  utmSource?: string,
  utmMedium?: string
): Promise<void> {
  const search = new URLSearchParams({ user_id: userId });
  if (utmSource) search.set('utm_source', utmSource);
  if (utmMedium) search.set('utm_medium', utmMedium);
  await apiRequest(`/${notificationId}/click?${search}`, { method: 'POST' });
}

// ── Offline Queue ─────────────────────────────────────────────────────────

const OFFLINE_QUEUE_KEY = 'safevix_notification_offline_queue';

export function getOfflineQueue(): OfflineNotification[] {
  try {
    const raw = localStorage.getItem(OFFLINE_QUEUE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

export function addToOfflineQueue(item: Omit<OfflineNotification, 'id' | 'createdAt'>): void {
  const queue = getOfflineQueue();
  queue.push({
    ...item,
    id: crypto.randomUUID ? crypto.randomUUID() : `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`,
    createdAt: Date.now(),
  });
  try {
    localStorage.setItem(OFFLINE_QUEUE_KEY, JSON.stringify(queue.slice(-100)));
  } catch {
    // localStorage full; discard oldest
  }
}

export function clearOfflineQueue(): void {
  try {
    localStorage.removeItem(OFFLINE_QUEUE_KEY);
  } catch {
    // ignore
  }
}

export async function syncOfflineQueue(): Promise<number> {
  const queue = getOfflineQueue();
  if (queue.length === 0) return 0;
  let synced = 0;
  for (const item of queue) {
    try {
      await sendNotification(
        item.userId,
        item.notification.channel,
        item.notification.title,
        item.notification.body,
        {
          category: item.notification.category,
          priority: item.notification.priority,
          source: 'offline_queue',
        },
      );
      synced++;
    } catch {
      // leave in queue for next sync
    }
  }
  if (synced === queue.length) {
    clearOfflineQueue();
  } else {
    const remaining = queue.slice(synced);
    localStorage.setItem(OFFLINE_QUEUE_KEY, JSON.stringify(remaining));
  }
  return synced;
}

// ── WebSocket Hook ─────────────────────────────────────────────────────────

const MAX_RECONNECT_DELAY = 30_000;

export function useNotificationWebSocket(userId: string | null) {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectRef = useRef<ReturnType<typeof setTimeout>>();
  const attemptRef = useRef(0);

  const connect = useCallback(() => {
    if (!userId) return;
    const wsUrl = `${BACKEND_URL.replace(/^http/, 'ws')}/api/v1/notifications/ws?user_id=${userId}`;
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      setConnected(true);
      attemptRef.current = 0;
    };

    ws.onclose = () => {
      setConnected(false);
      const delay = Math.min(1000 * Math.pow(2, attemptRef.current), MAX_RECONNECT_DELAY);
      attemptRef.current++;
      const jitter = delay * (0.5 + Math.random() * 0.5);
      reconnectRef.current = setTimeout(connect, jitter);
    };

    ws.onerror = () => {
      ws.close();
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'notification') {
          setNotifications((prev) => [data as Notification, ...prev]);
          // Request browser notification for desktop channel
          if (data.channel === 'desktop' && 'Notification' in window && Notification.permission === 'granted') {
            new Notification(data.title, {
              body: data.body || '',
              tag: data.id,
            });
          }
        } else if (data.type === 'ping') {
          ws.send(JSON.stringify({ type: 'pong' }));
        } else if (data.type === 'connected') {
          // Trigger offline queue sync on reconnect
          syncOfflineQueue().catch(() => {});
        }
      } catch {
        // ignore parse errors
      }
    };
  }, [userId]);

  useEffect(() => {
    connect();
    return () => {
      if (reconnectRef.current) clearTimeout(reconnectRef.current);
      if (wsRef.current) wsRef.current.close();
    };
  }, [connect]);

  const sendAck = useCallback((notificationId: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'ack', notification_id: notificationId }));
    }
  }, []);

  const sendMarkRead = useCallback((notificationId: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'mark_read', notification_id: notificationId }));
    }
  }, []);

  return { notifications, setNotifications, connected, sendAck, sendMarkRead };
}

// ── Utilities ─────────────────────────────────────────────────────────────

export function getNotificationIcon(category?: NotificationCategory): string {
  const icons: Record<string, string> = {
    system_health: 'HeartPulse',
    ai: 'Brain',
    security: 'Shield',
    performance: 'Gauge',
    update: 'ArrowUpCircle',
    maintenance: 'Wrench',
    incident: 'AlertTriangle',
    deployment: 'Rocket',
    usage: 'BarChart3',
    billing: 'CreditCard',
    issue: 'Bug',
    sos: 'Siren',
    emergency: 'Ambulance',
    challan: 'FileText',
    general: 'Bell',
  };
  return icons[category || 'general'] || 'Bell';
}

export function getNotificationColor(priority: NotificationPriority): string {
  const colors: Record<NotificationPriority, string> = {
    critical: 'text-red-500 bg-red-500/10 border-red-500/20',
    high: 'text-orange-500 bg-orange-500/10 border-orange-500/20',
    normal: 'text-blue-500 bg-blue-500/10 border-blue-500/20',
    low: 'text-gray-500 bg-gray-500/10 border-gray-500/20',
  };
  return colors[priority];
}

export function getTimeAgo(isoDate: string): string {
  const now = Date.now();
  const date = new Date(isoDate).getTime();
  const diff = now - date;
  const minutes = Math.floor(diff / 60000);
  const hours = Math.floor(diff / 3600000);
  const days = Math.floor(diff / 86400000);
  if (minutes < 1) return 'just now';
  if (minutes < 60) return `${minutes}m ago`;
  if (hours < 24) return `${hours}h ago`;
  if (days < 7) return `${days}d ago`;
  return new Date(isoDate).toLocaleDateString();
}

export function requestDesktopNotificationPermission(): Promise<boolean> {
  if (!('Notification' in window)) return Promise.resolve(false);
  if (Notification.permission === 'granted') return Promise.resolve(true);
  if (Notification.permission === 'denied') return Promise.resolve(false);
  return Notification.requestPermission().then((p) => p === 'granted');
}
