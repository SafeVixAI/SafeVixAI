// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

import React from 'react';
import { render } from '@testing-library/react';
import '@testing-library/jest-dom';

const mockSetConnectivity = jest.fn();
const mockUseAppStore = jest.fn();

jest.mock('@/lib/store', () => ({
  useAppStore: (selector: any) => mockUseAppStore(selector),
}));

jest.mock('zustand/react/shallow', () => ({
  useShallow: (fn: any) => fn,
}));

import { NetworkMonitor } from '../NetworkMonitor';

describe('NetworkMonitor', function() {
  beforeEach(function() {
    jest.clearAllMocks();
    mockUseAppStore.mockReturnValue({ setConnectivity: mockSetConnectivity });
  });

  it('sets connectivity to online when navigator.onLine is true', function() {
    Object.defineProperty(navigator, 'onLine', { configurable: true, value: true });
    render(<NetworkMonitor />);
    expect(mockSetConnectivity).toHaveBeenCalledWith('online');
  });

  it('sets connectivity to offline when navigator.onLine is false', function() {
    Object.defineProperty(navigator, 'onLine', { configurable: true, value: false });
    render(<NetworkMonitor />);
    expect(mockSetConnectivity).toHaveBeenCalledWith('offline');
  });

  it('listens for online event on window', function() {
    const addEventListenerSpy = jest.spyOn(window, 'addEventListener');
    Object.defineProperty(navigator, 'onLine', { configurable: true, value: true });
    render(<NetworkMonitor />);
    expect(addEventListenerSpy).toHaveBeenCalledWith('online', expect.any(Function));
    expect(addEventListenerSpy).toHaveBeenCalledWith('offline', expect.any(Function));
    addEventListenerSpy.mockRestore();
  });

  it('cleans up event listeners on unmount', function() {
    const removeEventListenerSpy = jest.spyOn(window, 'removeEventListener');
    Object.defineProperty(navigator, 'onLine', { configurable: true, value: true });
    const { unmount } = render(<NetworkMonitor />);
    unmount();
    expect(removeEventListenerSpy).toHaveBeenCalledWith('online', expect.any(Function));
    expect(removeEventListenerSpy).toHaveBeenCalledWith('offline', expect.any(Function));
    removeEventListenerSpy.mockRestore();
  });
});



