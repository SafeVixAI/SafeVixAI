// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
import { renderHook, waitFor } from '@testing-library/react';
import { useGeolocation } from '../geolocation';
import { useAppStore } from '../store';

function setBrowserLocationSupport({
  geolocation,
  permissionState,
}: {
  geolocation?: Partial<Geolocation> | null;
  permissionState?: PermissionState;
}) {
  Object.defineProperty(window, 'isSecureContext', {
    configurable: true,
    value: true,
  });
  Object.defineProperty(navigator, 'geolocation', {
    configurable: true,
    value: geolocation === undefined ? null : geolocation,
  });
  Object.defineProperty(navigator, 'permissions', {
    configurable: true,
    value:
      permissionState == null
        ? undefined
        : {
            query: jest.fn().mockResolvedValue({ state: permissionState }),
          },
  });
}

describe('useGeolocation', function() {
  afterEach(function() {
    jest.restoreAllMocks();
    Object.defineProperty(window, 'isSecureContext', { configurable: true, value: true });
    delete (navigator as any).geolocation;
    delete (navigator as any).permissions;
  });
  beforeEach(function() {
    jest.clearAllMocks();
    useAppStore.setState({
      gpsLocation: null,
      gpsError: null,
      locationTracking: true,
    });
  });

  it('reports unsupported browsers clearly', async function() {
    setBrowserLocationSupport({ geolocation: null });

    renderHook(() => useGeolocation());

    await waitFor(() => {
      expect(useAppStore.getState().gpsError).toBe('Geolocation not supported by your browser.');
    });
  });

  it('reports denied browser permission clearly', async function() {
    setBrowserLocationSupport({
      permissionState: 'denied',
      geolocation: {
        clearWatch: jest.fn(),
      },
    });

    renderHook(() => useGeolocation());

    await waitFor(() => {
      expect(useAppStore.getState().gpsError).toBe(
        'Location permission is blocked in the browser. Enable it and retry.'
      );
    });
  });

  it('reports geolocation timeout clearly', async function() {
    const timeoutError = { code: 3 } as GeolocationPositionError;
    setBrowserLocationSupport({
      geolocation: {
        getCurrentPosition: jest.fn((_success, error) => error?.(timeoutError)),
        watchPosition: jest.fn((_success, error) => {
          error?.(timeoutError);
          return 42;
        }),
        clearWatch: jest.fn(),
      },
    });

    renderHook(() => useGeolocation());

    await waitFor(() => {
      expect(useAppStore.getState().gpsError).toBe('Location request timed out. Please try again.');
    });
  });

  it('reports permission denied error code', async function() {
    const deniedError = { code: 1 } as GeolocationPositionError;
    setBrowserLocationSupport({
      permissionState: 'granted',
      geolocation: {
        getCurrentPosition: jest.fn((_success, error) => error?.(deniedError)),
        watchPosition: jest.fn((_success, error) => {
          error?.(deniedError);
          return 42;
        }),
        clearWatch: jest.fn(),
      },
    });

    renderHook(() => useGeolocation());

    await waitFor(() => {
      expect(useAppStore.getState().gpsError).toBe('Location permission denied. Please allow access in browser settings.');
    });
  });

  it('reports unavailable error code', async function() {
    const unavailableError = { code: 2 } as GeolocationPositionError;
    setBrowserLocationSupport({
      permissionState: 'granted',
      geolocation: {
        getCurrentPosition: jest.fn((_success, error) => error?.(unavailableError)),
        watchPosition: jest.fn((_success, error) => {
          error?.(unavailableError);
          return 42;
        }),
        clearWatch: jest.fn(),
      },
    });

    renderHook(() => useGeolocation());

    await waitFor(() => {
      expect(useAppStore.getState().gpsError).toBe('Location unavailable. Try again or check GPS signal.');
    });
  });

  it('handles successful geolocation', async function() {
    const pos = {
      coords: { latitude: 13.08, longitude: 80.27, accuracy: 30 },
      timestamp: 2000,
    } as GeolocationPosition;
    setBrowserLocationSupport({
      permissionState: 'granted',
      geolocation: {
        getCurrentPosition: jest.fn((success) => success?.(pos)),
        watchPosition: jest.fn((success) => {
          success?.(pos);
          return 42;
        }),
        clearWatch: jest.fn(),
      },
    });

    renderHook(() => useGeolocation());

    await waitFor(() => {
      expect(useAppStore.getState().gpsLocation?.lat).toBe(13.08);
    });
  });

  it('reports consent error when locationTracking is false', async function() {
    useAppStore.setState({ locationTracking: false })
    setBrowserLocationSupport({
      geolocation: {
        clearWatch: jest.fn(),
      },
    })
    renderHook(() => useGeolocation())
    await waitFor(() => {
      expect(useAppStore.getState().gpsError).toBe('Location tracking consent not granted. Enable location services in settings.')
    })
  })

  it('calls clearWatch on unmount', async function() {
    const clearWatch = jest.fn();
    setBrowserLocationSupport({
      permissionState: 'granted',
      geolocation: {
        getCurrentPosition: jest.fn((success) => success?.({ coords: { latitude: 13.0, longitude: 80.0, accuracy: 30 }, timestamp: 1000 } as GeolocationPosition)),
        watchPosition: jest.fn(() => 42),
        clearWatch: clearWatch,
      },
    });
    const { unmount } = renderHook(() => useGeolocation());
    await waitFor(() => {
      expect(useAppStore.getState().gpsLocation?.lat).toBe(13.0);
    });
    unmount();
    expect(clearWatch).toHaveBeenCalledWith(42);
  })

  it('calls resolvePosition when permissions query throws', async function() {
    setBrowserLocationSupport({
      permissionState: 'granted',
      geolocation: {
        getCurrentPosition: jest.fn((success) => success?.({ coords: { latitude: 12.0, longitude: 77.0, accuracy: 50 }, timestamp: 1000 } as GeolocationPosition)),
        watchPosition: jest.fn((success) => {
          success?.({ coords: { latitude: 12.0, longitude: 77.0, accuracy: 50 }, timestamp: 1000 } as GeolocationPosition);
          return 42;
        }),
        clearWatch: jest.fn(),
      },
    });
    Object.defineProperty(navigator, 'permissions', {
      configurable: true,
      value: {
        query: jest.fn().mockRejectedValue(new Error('permissions error')),
      },
    });

    renderHook(() => useGeolocation());

    await waitFor(() => {
      expect(useAppStore.getState().gpsLocation?.lat).toBe(12.0);
    });
  });
});


