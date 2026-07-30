// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';

const mockSetConnectivity = jest.fn();
const mockUseAppStore = jest.fn();

jest.mock('@/lib/store', () => ({
  useAppStore: (selector: any) => mockUseAppStore(selector),
}));

jest.mock('zustand/react/shallow', () => ({
  useShallow: (fn: any) => fn,
}));

import { ConnectivityProvider } from '../ConnectivityProvider';

describe('ConnectivityProvider', function() {
  beforeEach(function() {
    jest.clearAllMocks();
    mockUseAppStore.mockReturnValue({ setConnectivity: mockSetConnectivity });
    Object.defineProperty(navigator, 'onLine', { configurable: true, value: true });
  });

  it('renders children', function() {
    render(
      <ConnectivityProvider>
        <div data-testid="child">Hello</div>
      </ConnectivityProvider>
    );
    expect(screen.getByTestId('child')).toBeInTheDocument();
    expect(screen.getByText('Hello')).toBeInTheDocument();
  });

  it('wraps children in a fragment provider structure', function() {
    const { container } = render(
      <ConnectivityProvider>
        <span>foo</span>
        <span>bar</span>
      </ConnectivityProvider>
    );
    expect(container.firstChild).toBeInTheDocument();
    expect(container.children.length).toBe(2);
    expect(container.children[0].textContent).toBe('foo');
    expect(container.children[1].textContent).toBe('bar');
  });

  it('sets connectivity to offline when offline event fires', function() {
    Object.defineProperty(navigator, 'onLine', { configurable: true, value: false });
    render(
      <ConnectivityProvider>
        <div />
      </ConnectivityProvider>
    );
    window.dispatchEvent(new Event('offline'));
    expect(mockSetConnectivity).toHaveBeenCalledWith('offline');
  });

  it('sets connectivity to online when online event fires', function() {
    render(
      <ConnectivityProvider>
        <div />
      </ConnectivityProvider>
    );
    window.dispatchEvent(new Event('online'));
    expect(mockSetConnectivity).toHaveBeenCalledWith('online');
  });
});



