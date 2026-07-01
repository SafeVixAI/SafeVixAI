import { renderHook } from '@testing-library/react';
import { useAppStore, useGpsLocation, useGpsError, useSetGpsLocation, useSetGpsError, useNearbyServices, useServiceRadius, useServiceCategory, useServiceSearchMeta, useNearbyRoadIssues, useRoadIssueSearchMeta, useAiMode, useModelLoadProgress, useConnectivity, useServerWarming, useShowHazardHeatmap, useShowSatellite, useShowTraffic, useShowSafeSpaces, useShowEmergencyServices, useMapStatus, useMapProvider, useMapError, useMapSearchTarget, useUserProfile, useDrivingScore, useCrashDetectionEnabled, useSpeedAlert, useHazardNotifs, useLocationTracking, useSosVibration, useAutoOffline, useAnalyticsOptIn, useNavApp, useIsDesktopSidebarCollapsed, useIsThinSidebarEnabled, useSoundsEnabled, useChallanState, useIsAuthenticated, useOperatorName, useAuthToken, useAuthRole, useSelectedProvider, useActiveFallbackChain, useProviderSyncStatus } from '../store';

function resetStore() {
  localStorage.clear();
  useAppStore.setState({
    gpsLocation: null,
    gpsError: null,
    nearbyServices: [],
    serviceRadius: 5000,
    serviceCategory: 'All',
    serviceSearchMeta: { radiusUsed: 5000, count: 0, coords: null },
    nearbyRoadIssues: [],
    roadIssueSearchMeta: { radiusUsed: 5000, count: 0, coords: null },
    aiMode: 'cloud',
    modelLoadProgress: null,
    connectivity: 'online',
    serverWarming: false,
    showHazardHeatmap: false,
    showSatellite: false,
    showTraffic: false,
    showSafeSpaces: false,
    showEmergencyServices: false,
    mapStatus: 'loading' as const,
    mapProvider: null,
    mapError: null,
    mapSearchTarget: null,
    userProfile: { id: '', name: '', phone: '', bloodGroup: '', vehicleNumber: '', emergencyContact: '', emergencyContacts: [], medicalConditions: '', preferredLanguage: 'en' },
    drivingScore: 85,
    crashDetectionEnabled: true,
    speedAlert: true,
    hazardNotifs: true,
    locationTracking: false,
    sosVibration: true,
    autoOffline: false,
    analyticsOptIn: false,
    navApp: 'google-maps',
    isDesktopSidebarCollapsed: false,
    isThinSidebarEnabled: false,
    soundsEnabled: true,
    challanState: null,
    isAuthenticated: false,
    operatorName: '',
    authToken: null,
    authRole: null,
    selectedProvider: 'groq',
    activeFallbackChain: [],
    providerSyncStatus: 'idle',
  });
}

describe('app store persistence', function() {
  beforeEach(function() {
    localStorage.clear();
    useAppStore.setState({
      isAuthenticated: false,
      operatorName: '',
      mapStatus: 'loading',
      mapProvider: null,
      mapError: null,
      mapSearchTarget: null,
      userProfile: {
        id: '',
        name: '',
        phone: '',
        bloodGroup: '',
        vehicleNumber: '',
        emergencyContact: '',
        emergencyContacts: [],
        medicalConditions: '',
        preferredLanguage: 'en',
      },
    });
  });

  it('persists operator auth state across sessions', function() {
    useAppStore.getState().setAuth('Operator');
    var persisted = JSON.parse(localStorage.getItem('svai-storage') ?? '{}');
    expect(useAppStore.getState().operatorName).toBe('Operator');
    expect(persisted.state?.operatorName).toBe('Operator');
    expect(persisted.state?.isAuthenticated).toBe(true);
  });

  it('persists non-sensitive emergency profile fields', function() {
    useAppStore.getState().setUserProfile({
      name: 'Demo User',
      bloodGroup: 'O+',
      emergencyContact: '+919999999999',
      vehicleNumber: 'TN01AB1234',
    });
    var persisted = JSON.parse(localStorage.getItem('svai-storage') ?? '{}');
    expect(persisted.state?.userProfile).toBeUndefined();
    expect(useAppStore.getState().userProfile).toEqual(expect.objectContaining({
      name: 'Demo User',
      bloodGroup: 'O+',
      emergencyContact: '+919999999999',
      vehicleNumber: 'TN01AB1234',
    }));
  });

  it('keeps transient map state out of persisted storage', function() {
    useAppStore.getState().setMapState({
      mapStatus: 'ready',
      mapProvider: 'maptiler-vector',
      mapError: null,
    });
    useAppStore.getState().setMapSearchTarget({
      lat: 13.0827,
      lon: 80.2707,
      label: 'Chennai',
      timestamp: 123,
    });
    var persisted = JSON.parse(localStorage.getItem('svai-storage') ?? '{}');
    expect(useAppStore.getState().mapProvider).toBe('maptiler-vector');
    expect(useAppStore.getState().mapSearchTarget?.label).toBe('Chennai');
    expect(persisted.state?.mapStatus).toBeUndefined();
    expect(persisted.state?.mapProvider).toBeUndefined();
    expect(persisted.state?.mapSearchTarget).toBeUndefined();
  });

  it('handles merge with persisted state that has userProfile', function() {
    localStorage.setItem('svai-storage', JSON.stringify({
      state: { userProfile: { name: 'Old' }, operatorName: 'Test' },
      version: 0,
    }));
    useAppStore.getState().setAuth('Test');
    var state = useAppStore.getState();
    expect(state.userProfile?.name).not.toBe('Old');
    expect(state.operatorName).toBe('Test');
  });

  it('handles partialize excludes gpsLocation', function() {
    useAppStore.getState().setGpsLocation({ lat: 13.0, lon: 80.0, accuracy: 10 });
    var persisted = JSON.parse(localStorage.getItem('svai-storage') ?? '{}');
    expect(persisted.state?.gpsLocation).toBeUndefined();
  });
});

describe('granular selectors', function() {
  beforeEach(resetStore);

  it('useGpsLocation returns gpsLocation', function() {
    var { result } = renderHook(() => useGpsLocation());
    expect(result.current).toBeNull();
    useAppStore.getState().setGpsLocation({ lat: 13.0, lon: 80.0, accuracy: 10 });
    var { result: r2 } = renderHook(() => useGpsLocation());
    expect(r2.current?.lat).toBe(13.0);
  });

  it('useGpsError returns gpsError', function() {
    var { result } = renderHook(() => useGpsError());
    expect(result.current).toBeNull();
    useAppStore.getState().setGpsError('error');
    var { result: r2 } = renderHook(() => useGpsError());
    expect(r2.current).toBe('error');
  });

  it('useSetGpsLocation returns setGpsLocation function', function() {
    var { result } = renderHook(() => useSetGpsLocation());
    expect(typeof result.current).toBe('function');
  });

  it('useSetGpsError returns setGpsError function', function() {
    var { result } = renderHook(() => useSetGpsError());
    expect(typeof result.current).toBe('function');
  });

  it('useNearbyServices returns nearbyServices', function() {
    var { result } = renderHook(() => useNearbyServices());
    expect(result.current).toEqual([]);
  });

  it('useServiceRadius returns serviceRadius', function() {
    var { result } = renderHook(() => useServiceRadius());
    expect(result.current).toBe(5000);
  });

  it('useServiceCategory returns serviceCategory', function() {
    var { result } = renderHook(() => useServiceCategory());
    expect(result.current).toBe('All');
  });

  it('useServiceSearchMeta returns serviceSearchMeta', function() {
    var { result } = renderHook(() => useServiceSearchMeta());
    expect(result.current.radiusUsed).toBe(5000);
  });

  it('useNearbyRoadIssues returns nearbyRoadIssues', function() {
    var { result } = renderHook(() => useNearbyRoadIssues());
    expect(result.current).toEqual([]);
  });

  it('useRoadIssueSearchMeta returns roadIssueSearchMeta', function() {
    var { result } = renderHook(() => useRoadIssueSearchMeta());
    expect(result.current.count).toBe(0);
  });

  it('useAiMode returns aiMode', function() {
    var { result } = renderHook(() => useAiMode());
    expect(result.current).toBe('cloud');
  });

  it('useModelLoadProgress returns modelLoadProgress', function() {
    var { result } = renderHook(() => useModelLoadProgress());
    expect(result.current).toBeNull();
  });

  it('useConnectivity returns connectivity', function() {
    var { result } = renderHook(() => useConnectivity());
    expect(result.current).toBe('online');
  });

  it('useServerWarming returns serverWarming', function() {
    var { result } = renderHook(() => useServerWarming());
    expect(result.current).toBe(false);
  });

  it('useShowHazardHeatmap returns showHazardHeatmap', function() {
    var { result } = renderHook(() => useShowHazardHeatmap());
    expect(result.current).toBe(false);
  });

  it('useShowSatellite returns showSatellite', function() {
    var { result } = renderHook(() => useShowSatellite());
    expect(result.current).toBe(false);
  });

  it('useShowTraffic returns showTraffic', function() {
    var { result } = renderHook(() => useShowTraffic());
    expect(result.current).toBe(false);
  });

  it('useShowSafeSpaces returns showSafeSpaces', function() {
    var { result } = renderHook(() => useShowSafeSpaces());
    expect(result.current).toBe(false);
  });

  it('useShowEmergencyServices returns showEmergencyServices', function() {
    var { result } = renderHook(() => useShowEmergencyServices());
    expect(result.current).toBe(false);
  });

  it('useMapStatus returns mapStatus', function() {
    var { result } = renderHook(() => useMapStatus());
    expect(result.current).toBe('loading');
  });

  it('useMapProvider returns mapProvider', function() {
    var { result } = renderHook(() => useMapProvider());
    expect(result.current).toBeNull();
  });

  it('useMapError returns mapError', function() {
    var { result } = renderHook(() => useMapError());
    expect(result.current).toBeNull();
  });

  it('useMapSearchTarget returns mapSearchTarget', function() {
    var { result } = renderHook(() => useMapSearchTarget());
    expect(result.current).toBeNull();
  });

  it('useUserProfile returns userProfile', function() {
    var { result } = renderHook(() => useUserProfile());
    expect(result.current.name).toBe('');
  });

  it('useDrivingScore returns drivingScore', function() {
    var { result } = renderHook(() => useDrivingScore());
    expect(result.current).toBe(85);
  });

  it('useCrashDetectionEnabled returns crashDetectionEnabled', function() {
    var { result } = renderHook(() => useCrashDetectionEnabled());
    expect(result.current).toBe(true);
  });

  it('useSpeedAlert returns speedAlert', function() {
    var { result } = renderHook(() => useSpeedAlert());
    expect(result.current).toBe(true);
  });

  it('useHazardNotifs returns hazardNotifs', function() {
    var { result } = renderHook(() => useHazardNotifs());
    expect(result.current).toBe(true);
  });

  it('useLocationTracking returns locationTracking', function() {
    var { result } = renderHook(() => useLocationTracking());
    expect(result.current).toBe(false);
  });

  it('useSosVibration returns sosVibration', function() {
    var { result } = renderHook(() => useSosVibration());
    expect(result.current).toBe(true);
  });

  it('useAutoOffline returns autoOffline', function() {
    var { result } = renderHook(() => useAutoOffline());
    expect(result.current).toBe(false);
  });

  it('useAnalyticsOptIn returns analyticsOptIn', function() {
    var { result } = renderHook(() => useAnalyticsOptIn());
    expect(result.current).toBe(false);
  });

  it('useNavApp returns navApp', function() {
    var { result } = renderHook(() => useNavApp());
    expect(result.current).toBe('google-maps');
  });

  it('useIsDesktopSidebarCollapsed returns isDesktopSidebarCollapsed', function() {
    var { result } = renderHook(() => useIsDesktopSidebarCollapsed());
    expect(result.current).toBe(false);
  });

  it('useIsThinSidebarEnabled returns isThinSidebarEnabled', function() {
    var { result } = renderHook(() => useIsThinSidebarEnabled());
    expect(result.current).toBe(false);
  });

  it('useSoundsEnabled returns soundsEnabled', function() {
    var { result } = renderHook(() => useSoundsEnabled());
    expect(result.current).toBe(true);
  });

  it('useChallanState returns challanState', function() {
    var { result } = renderHook(() => useChallanState());
    expect(result.current).toBeNull();
  });

  it('useIsAuthenticated returns isAuthenticated', function() {
    var { result } = renderHook(() => useIsAuthenticated());
    expect(result.current).toBe(false);
  });

  it('useOperatorName returns operatorName', function() {
    var { result } = renderHook(() => useOperatorName());
    expect(result.current).toBe('');
  });

  it('useAuthToken returns authToken', function() {
    var { result } = renderHook(() => useAuthToken());
    expect(result.current).toBeNull();
  });

  it('useAuthRole returns authRole', function() {
    var { result } = renderHook(() => useAuthRole());
    expect(result.current).toBeNull();
  });

  it('useSelectedProvider returns selectedProvider', function() {
    var { result } = renderHook(() => useSelectedProvider());
    expect(result.current).toBe('groq');
  });

  it('useActiveFallbackChain returns activeFallbackChain', function() {
    var { result } = renderHook(() => useActiveFallbackChain());
    expect(result.current).toEqual([]);
  });

  it('useProviderSyncStatus returns providerSyncStatus', function() {
    var { result } = renderHook(() => useProviderSyncStatus());
    expect(result.current).toBe('idle');
  });
});
