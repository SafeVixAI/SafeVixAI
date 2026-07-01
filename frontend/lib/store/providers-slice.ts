import type { StateCreator } from 'zustand';

export interface ProviderSelection {
  providerName: string;
  model: string;
  displayName: string;
}

export type SyncStatus = 'idle' | 'syncing' | 'success' | 'error';

export interface ProvidersSlice {
  selectedProvider: ProviderSelection | null;
  setSelectedProvider: (p: ProviderSelection | null) => void;
  activeFallbackChain: string[];
  setActiveFallbackChain: (chain: string[]) => void;
  providerSyncStatus: SyncStatus;
  setProviderSyncStatus: (status: SyncStatus) => void;
}

export const createProvidersSlice: StateCreator<any, [], [], ProvidersSlice> = (set) => ({
  selectedProvider: null,
  setSelectedProvider: (p) => set({ selectedProvider: p }),
  activeFallbackChain: [],
  setActiveFallbackChain: (chain) => set({ activeFallbackChain: chain }),
  providerSyncStatus: 'idle',
  setProviderSyncStatus: (status) => set({ providerSyncStatus: status }),
});
