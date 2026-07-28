// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

import { renderHook, act } from '@testing-library/react';
import { useServiceWorkerUpdate } from '@/hooks/useServiceWorkerUpdate';

describe('useServiceWorkerUpdate', function () {
  var mockWaiting: ServiceWorker;
  var mockRegistration: ServiceWorkerRegistration;
  var addEventListenerCallbacks: Record<string, Function>;

  beforeEach(function () {
    addEventListenerCallbacks = {};
    mockWaiting = {
      postMessage: jest.fn(),
      state: 'installed',
    } as unknown as ServiceWorker;

    mockRegistration = {
      waiting: mockWaiting,
      installing: null,
      addEventListener: jest.fn(function (event: string, cb: Function) {
        addEventListenerCallbacks[event] = cb;
      }),
    } as ServiceWorkerRegistration;

    Object.defineProperty(navigator, 'serviceWorker', {
      value: {
        controller: {} as ServiceWorker,
        getRegistration: jest.fn().mockResolvedValue(mockRegistration),
        addEventListener: jest.fn(),
        removeEventListener: jest.fn(),
      },
      writable: true,
      configurable: true,
    });

    localStorage.clear();
  });

  it('detects waiting service worker', function () {
    var { result } = renderHook(function () { return useServiceWorkerUpdate(); });
    expect(result.current.updateAvailable).toBe(true);
    expect(result.current.waitingSw).toBe(mockWaiting);
  });

  it('applyUpdate sends SKIP_WAITING and reloads', function () {
    var { result } = renderHook(function () { return useServiceWorkerUpdate(); });
    act(function () {
      result.current.applyUpdate();
    });
    expect(mockWaiting.postMessage).toHaveBeenCalledWith({ action: 'SKIP_WAITING' });
  });

  it('dismissUpdate sets localStorage', function () {
    var { result } = renderHook(function () { return useServiceWorkerUpdate(); });
    act(function () {
      result.current.dismissUpdate();
    });
    var val = localStorage.getItem('pwa_update_dismissed');
    expect(val).not.toBeNull();
  });

  it('respects 24h cooldown after dismiss', function () {
    localStorage.setItem('pwa_update_dismissed', Date.now().toString());
    var { result } = renderHook(function () { return useServiceWorkerUpdate(); });
    expect(result.current.updateAvailable).toBe(false);
  });

  it('returns no update when no SW present', function () {
    Object.defineProperty(navigator, 'serviceWorker', {
      value: {
        getRegistration: jest.fn().mockResolvedValue(null),
        addEventListener: jest.fn(),
        removeEventListener: jest.fn(),
      },
      writable: true,
      configurable: true,
    });
    var { result } = renderHook(function () { return useServiceWorkerUpdate(); });
    expect(result.current.updateAvailable).toBe(false);
    expect(result.current.waitingSw).toBeNull();
  });
});
