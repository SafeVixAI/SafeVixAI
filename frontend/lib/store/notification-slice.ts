// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

import { create } from 'zustand';
import { subscribeWithSelector } from 'zustand/middleware';
import type { Notification } from '@/lib/notifications';

interface NotificationState {
  items: Notification[];
  unreadCount: number;
  isCenterOpen: boolean;
  preferencesOpen: boolean;
  soundEnabled: boolean;
  desktopEnabled: boolean;

  setItems: (items: Notification[]) => void;
  addItem: (item: Notification) => void;
  removeItem: (id: string) => void;
  setUnreadCount: (count: number) => void;
  markAsRead: (id: string) => void;
  markAllAsRead: () => void;
  setCenterOpen: (open: boolean) => void;
  toggleCenter: () => void;
  setPreferencesOpen: (open: boolean) => void;
  toggleSound: () => void;
  toggleDesktop: () => void;
}

export const useNotificationStore = create<NotificationState>()(
  subscribeWithSelector((set, get) => ({
    items: [],
    unreadCount: 0,
    isCenterOpen: false,
    preferencesOpen: false,
    soundEnabled: true,
    desktopEnabled: true,

    setItems: (items) => set({ items }),

    addItem: (item) => {
      const exists = get().items.some((n) => n.id === item.id);
      if (exists) return;
      set((state) => ({
        items: [item, ...state.items],
        unreadCount: state.unreadCount + 1,
      }));
      if (get().soundEnabled) {
        try {
          const audio = new Audio('/sounds/notification.mp3');
          audio.volume = 0.3;
          audio.play().catch(() => {});
        } catch {
          // audio not available
        }
      }
    },

    removeItem: (id) =>
      set((state) => ({
        items: state.items.filter((n) => n.id !== id),
        unreadCount: state.unreadCount - 1,
      })),

    setUnreadCount: (count) => set({ unreadCount: count }),

    markAsRead: (id) =>
      set((state) => ({
        items: state.items.map((n) =>
          n.id === id ? { ...n, status: 'read' as const } : n
        ),
        unreadCount: Math.max(0, state.unreadCount - 1),
      })),

    markAllAsRead: () =>
      set((state) => ({
        items: state.items.map((n) => ({
          ...n,
          status: 'read' as const,
          read_at: new Date().toISOString(),
        })),
        unreadCount: 0,
      })),

    setCenterOpen: (open) => set({ isCenterOpen: open }),
    toggleCenter: () => set((state) => ({ isCenterOpen: !state.isCenterOpen })),
    setPreferencesOpen: (open) => set({ preferencesOpen: open }),
    toggleSound: () => set((state) => ({ soundEnabled: !state.soundEnabled })),
    toggleDesktop: () => set((state) => ({ desktopEnabled: !state.desktopEnabled })),
  }))
);
