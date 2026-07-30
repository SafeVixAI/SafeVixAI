// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

import React from 'react';
import { render, screen, act, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { ThemeProvider, useTheme } from '../ThemeProvider';

let mqListeners: Function[] = [];
let mqMatches = false;

beforeEach(function() {
  mqListeners = [];
  mqMatches = false;
  Object.defineProperty(window, 'matchMedia', {
    writable: true,
    value: jest.fn().mockImplementation((query) => ({
      matches: mqMatches,
      media: query,
      onchange: null,
      addEventListener: function(_: string, fn: Function) { mqListeners.push(fn) },
      removeEventListener: jest.fn(),
      dispatchEvent: jest.fn(),
    })),
  });
});

function TestConsumer() {
  const { theme, resolvedTheme, setTheme } = useTheme();
  return (
    <div>
      <span data-testid="theme">{theme}</span>
      <span data-testid="resolved">{resolvedTheme}</span>
      <button data-testid="set-dark" onClick={() => setTheme('dark')}>Dark</button>
      <button data-testid="set-light" onClick={() => setTheme('light')}>Light</button>
      <button data-testid="set-system" onClick={() => setTheme('system')}>System</button>
    </div>
  );
}

function renderWithTheme(ui: React.ReactElement) {
  return render(<ThemeProvider>{ui}</ThemeProvider>);
}

describe('ThemeProvider', function() {
  beforeEach(function() {
    localStorage.clear();
    document.documentElement.removeAttribute('data-theme');
    document.documentElement.classList.remove('dark', 'light');
  });

  it('renders children', function() {
    renderWithTheme(<div data-testid="child">hello</div>);
    expect(screen.getByTestId('child')).toBeInTheDocument();
  });

  it('provides default theme as system', function() {
    renderWithTheme(<TestConsumer />);
    expect(screen.getByTestId('theme')).toHaveTextContent('system');
  });

  it('sets theme to dark via setTheme', function() {
    renderWithTheme(<TestConsumer />);
    act(() => { fireEvent.click(screen.getByTestId('set-dark')); });
    expect(screen.getByTestId('theme')).toHaveTextContent('dark');
    expect(localStorage.getItem('svai-theme')).toBe('dark');
  });

  it('sets theme to light via setTheme', function() {
    renderWithTheme(<TestConsumer />);
    act(() => { fireEvent.click(screen.getByTestId('set-light')); });
    expect(screen.getByTestId('theme')).toHaveTextContent('light');
    expect(localStorage.getItem('svai-theme')).toBe('light');
  });

  it('sets theme to system via setTheme', function() {
    renderWithTheme(<TestConsumer />);
    act(() => { fireEvent.click(screen.getByTestId('set-system')); });
    expect(screen.getByTestId('theme')).toHaveTextContent('system');
    expect(localStorage.getItem('svai-theme')).toBe('system');
  });

  it('updates data-theme attribute on root', function() {
    renderWithTheme(<TestConsumer />);
    act(() => { fireEvent.click(screen.getByTestId('set-dark')); });
    expect(document.documentElement.getAttribute('data-theme')).toBe('dark');
  });

  it('toggles dark class on root', function() {
    renderWithTheme(<TestConsumer />);
    act(() => { fireEvent.click(screen.getByTestId('set-dark')); });
    expect(document.documentElement.classList.contains('dark')).toBe(true);
    expect(document.documentElement.classList.contains('light')).toBe(false);
  });

  it('toggles light class on root', function() {
    renderWithTheme(<TestConsumer />);
    act(() => { fireEvent.click(screen.getByTestId('set-light')); });
    expect(document.documentElement.classList.contains('light')).toBe(true);
    expect(document.documentElement.classList.contains('dark')).toBe(false);
  });

  it('resolves theme correctly', function() {
    renderWithTheme(<TestConsumer />);
    act(() => { fireEvent.click(screen.getByTestId('set-dark')); });
    expect(screen.getByTestId('resolved')).toHaveTextContent('dark');
  });

  it('loads saved theme from localStorage', function() {
    localStorage.setItem('svai-theme', 'light');
    renderWithTheme(<TestConsumer />);
    expect(screen.getByTestId('theme')).toHaveTextContent('light');
  });

  it('resolves to light when system prefers light and theme is system', function() {
    mqMatches = true;
    renderWithTheme(<TestConsumer />);
    expect(screen.getByTestId('resolved')).toHaveTextContent('light');
    expect(document.documentElement.getAttribute('data-theme')).toBe('light');
  });

  it('re-applies system theme when matchMedia change fires and theme is system', function() {
    renderWithTheme(<TestConsumer />);
    act(() => { fireEvent.click(screen.getByTestId('set-system')); });
    expect(mqListeners.length).toBeGreaterThanOrEqual(1);
    act(() => { mqListeners[mqListeners.length - 1](); });
    expect(document.documentElement.getAttribute('data-theme')).toBe('dark');
  });

  it('skips re-apply when matchMedia change fires but theme is not system', function() {
    renderWithTheme(<TestConsumer />);
    act(() => { fireEvent.click(screen.getByTestId('set-dark')); });
    // Fire only the last (active) listener — it should have theme='dark' in its closure
    const lastListener = mqListeners[mqListeners.length - 1];
    act(() => { lastListener(); });
    expect(document.documentElement.getAttribute('data-theme')).toBe('dark');
  });
});


