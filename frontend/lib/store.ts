// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { loadUserProfileFromIndexedDB } from './profile-storage';
import { markHydrated } from './use-hydrated';
import { createAuthSlice } from './store/auth-slice';
import { createMapSlice } from './store/map-slice';
import { createSettingsSlice } from './store/settings-slice';
import { createUISlice } from './store/ui-slice';
import { createDataSlice } from './store/data-slice';
import { createProvidersSlice } from './store/providers-slice';
import type { AppState } from './store/types';

export const useAppStore = create<AppState>()(
  persist(
    (...a) => ({
      ...createAuthSlice(...a),
      ...createMapSlice(...a),
      ...createSettingsSlice(...a),
      ...createUISlice(...a),
      ...createDataSlice(...a),
      ...createProvidersSlice(...a),
    }),
    {
      name: 'svai-storage',
      merge: (persistedState, currentState) => {
        const state = persistedState as Partial<AppState> | undefined;
        if (state && 'userProfile' in state) {
          delete state.userProfile;
        }
        return { ...currentState, ...state };
      },
      onRehydrateStorage: () => {
        return (state, error) => {
          markHydrated();
          if (!error) {
            loadUserProfileFromIndexedDB().then((profile) => {
              if (profile) {
                useAppStore.getState().setUserProfile(profile);
              }
              useAppStore.getState().setProfileHydrated(true);
            });
          }
        };
      },
      partialize: (state) => ({
        aiMode: state.aiMode,
        serviceCategory: state.serviceCategory,
        isDesktopSidebarCollapsed: state.isDesktopSidebarCollapsed,
        isThinSidebarEnabled: state.isThinSidebarEnabled,
        showHazardHeatmap: state.showHazardHeatmap,
        showSatellite: state.showSatellite,
        showTraffic: state.showTraffic,
        showSafeSpaces: state.showSafeSpaces,
        showEmergencyServices: state.showEmergencyServices,
        soundsEnabled: state.soundsEnabled,
        speedAlert: state.speedAlert,
        hazardNotifs: state.hazardNotifs,
        locationTracking: state.locationTracking,
        sosVibration: state.sosVibration,
        autoOffline: state.autoOffline,
        analyticsOptIn: state.analyticsOptIn,
        navApp: state.navApp,
        isAuthenticated: state.isAuthenticated,
        operatorName: state.operatorName,
        authRole: state.authRole,
        selectedProvider: state.selectedProvider,
        activeFallbackChain: state.activeFallbackChain,
      }),
    }
  )
);

export type {
  GpsLocation, NearbyService, NearbyRoadIssue,
  ServiceSearchMeta, RoadIssueSearchMeta, UserProfile,
  AiMode, ConnectivityState, MapStatus, MapProvider, MapSearchTarget,
} from './store/types';

// ── Granular Selectors ──

// GPS
export const useGpsLocation = () => useAppStore((s) => s.gpsLocation);
export const useGpsError = () => useAppStore((s) => s.gpsError);
export const useSetGpsLocation = () => useAppStore((s) => s.setGpsLocation);
export const useSetGpsError = () => useAppStore((s) => s.setGpsError);

// Services
export const useNearbyServices = () => useAppStore((s) => s.nearbyServices);
export const useServiceRadius = () => useAppStore((s) => s.serviceRadius);
export const useServiceCategory = () => useAppStore((s) => s.serviceCategory);
export const useServiceSearchMeta = () => useAppStore((s) => s.serviceSearchMeta);
export const useNearbyRoadIssues = () => useAppStore((s) => s.nearbyRoadIssues);
export const useRoadIssueSearchMeta = () => useAppStore((s) => s.roadIssueSearchMeta);

// AI / Connectivity
export const useAiMode = () => useAppStore((s) => s.aiMode);
export const useModelLoadProgress = () => useAppStore((s) => s.modelLoadProgress);
export const useConnectivity = () => useAppStore((s) => s.connectivity);
export const useServerWarming = () => useAppStore((s) => s.serverWarming);

// Map layers
export const useShowHazardHeatmap = () => useAppStore((s) => s.showHazardHeatmap);
export const useShowSatellite = () => useAppStore((s) => s.showSatellite);
export const useShowTraffic = () => useAppStore((s) => s.showTraffic);
export const useShowSafeSpaces = () => useAppStore((s) => s.showSafeSpaces);
export const useShowEmergencyServices = () => useAppStore((s) => s.showEmergencyServices);
export const useMapStatus = () => useAppStore((s) => s.mapStatus);
export const useMapProvider = () => useAppStore((s) => s.mapProvider);
export const useMapError = () => useAppStore((s) => s.mapError);
export const useMapSearchTarget = () => useAppStore((s) => s.mapSearchTarget);

// User profile
export const useUserProfile = () => useAppStore((s) => s.userProfile);
export const useDrivingScore = () => useAppStore((s) => s.drivingScore);
export const useCrashDetectionEnabled = () => useAppStore((s) => s.crashDetectionEnabled);

// Settings
export const useSpeedAlert = () => useAppStore((s) => s.speedAlert);
export const useHazardNotifs = () => useAppStore((s) => s.hazardNotifs);
export const useLocationTracking = () => useAppStore((s) => s.locationTracking);
export const useSosVibration = () => useAppStore((s) => s.sosVibration);
export const useAutoOffline = () => useAppStore((s) => s.autoOffline);
export const useAnalyticsOptIn = () => useAppStore((s) => s.analyticsOptIn);
export const useNavApp = () => useAppStore((s) => s.navApp);

// UI
export const useIsDesktopSidebarCollapsed = () => useAppStore((s) => s.isDesktopSidebarCollapsed);
export const useIsThinSidebarEnabled = () => useAppStore((s) => s.isThinSidebarEnabled);
export const useSoundsEnabled = () => useAppStore((s) => s.soundsEnabled);
export const useChallanState = () => useAppStore((s) => s.challanState);

// Auth
export const useIsAuthenticated = () => useAppStore((s) => s.isAuthenticated);
export const useOperatorName = () => useAppStore((s) => s.operatorName);
export const useAuthToken = () => useAppStore((s) => s.authToken);
export const useAuthRole = () => useAppStore((s) => s.authRole);

// Providers
export const useSelectedProvider = () => useAppStore((s) => s.selectedProvider);
export const useActiveFallbackChain = () => useAppStore((s) => s.activeFallbackChain);
export const useProviderSyncStatus = () => useAppStore((s) => s.providerSyncStatus);
