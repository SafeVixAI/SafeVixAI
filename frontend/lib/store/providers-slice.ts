import type { StateCreator } from 'zustand';

export interface ProviderSelection {
  providerName: string;
  model: string;
  displayName: string;
}

export interface ProvidersSlice {
  selectedProvider: ProviderSelection | null;
  setSelectedProvider: (p: ProviderSelection | null) => void;
}

export const createProvidersSlice: StateCreator<any, [], [], ProvidersSlice> = (set) => ({
  selectedProvider: null,
  setSelectedProvider: (p) => set({ selectedProvider: p }),
});
