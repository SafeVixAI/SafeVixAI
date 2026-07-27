// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

import type { StateCreator } from 'zustand';

export type ReleaseChannel = 'stable' | 'beta' | 'nightly' | 'pre-release';
export type UpdateStatus = 'up-to-date' | 'available' | 'downloading' | 'installing' | 'installed' | 'error';

export interface UpdateInfo {
  currentVersion: string;
  latestVersion: string | null;
  updateAvailable: boolean;
  channel: ReleaseChannel;
  isMandatory: boolean;
  isSecurity: boolean;
  lastCheckedAt: string | null;
  downloadProgress: number;
  retryCount: number;
  maxRetries: number;
  status: UpdateStatus;
}

export interface UpdateSlice {
  updateInfo: UpdateInfo;
  updateBannerDismissed: boolean;
  setUpdateInfo: (info: Partial<UpdateInfo>) => void;
  dismissUpdateBanner: () => void;
  resetUpdateBanner: () => void;
  setDownloadProgress: (progress: number) => void;
  setUpdateStatus: (status: UpdateStatus) => void;
  incrementRetry: () => void;
  resetRetry: () => void;
}

const DEFAULT_UPDATE_INFO: UpdateInfo = {
  currentVersion: '1.0.0',
  latestVersion: null,
  updateAvailable: false,
  channel: 'stable',
  isMandatory: false,
  isSecurity: false,
  lastCheckedAt: null,
  downloadProgress: 0,
  retryCount: 0,
  maxRetries: 3,
  status: 'up-to-date',
};

export const createUpdateSlice: StateCreator<any, [], [], UpdateSlice> = (set) => ({
  updateInfo: { ...DEFAULT_UPDATE_INFO },
  updateBannerDismissed: false,
  setUpdateInfo: (info) =>
    set((state: any) => ({
      updateInfo: { ...state.updateInfo, ...info },
    })),
  dismissUpdateBanner: () => set({ updateBannerDismissed: true }),
  resetUpdateBanner: () => set({ updateBannerDismissed: false }),
  setDownloadProgress: (progress) =>
    set((state: any) => ({
      updateInfo: { ...state.updateInfo, downloadProgress: progress },
    })),
  setUpdateStatus: (status) =>
    set((state: any) => ({
      updateInfo: { ...state.updateInfo, status },
    })),
  incrementRetry: () =>
    set((state: any) => ({
      updateInfo: { ...state.updateInfo, retryCount: state.updateInfo.retryCount + 1 },
    })),
  resetRetry: () =>
    set((state: any) => ({
      updateInfo: { ...state.updateInfo, retryCount: 0 },
    })),
});
