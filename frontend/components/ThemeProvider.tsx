'use client';

// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team


import { createContext, useContext, useEffect, useState, ReactNode } from 'react';

type Theme = 'dark' | 'light' | 'system';

interface ThemeContextValue {
  theme: Theme;
  resolvedTheme: 'dark' | 'light';
  setTheme: (_t: Theme) => void;
}

const ThemeContext = createContext<ThemeContextValue>({
  theme: 'system',
  resolvedTheme: 'dark',
  setTheme: () => {},
});

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setThemeState] = useState<Theme>('system');
  const [resolvedTheme, setResolvedTheme] = useState<'dark' | 'light'>('dark');

  useEffect(() => {
    // Load saved theme from localStorage
    const saved = (localStorage.getItem('svai-theme') ?? 'system') as Theme;
    setThemeState(saved);
  }, []);

  useEffect(() => {
    const root = document.documentElement;
    const mq = window.matchMedia('(prefers-color-scheme: light)');

    const apply = (t: Theme) => {
      const effective = t === 'system'
        ? (mq.matches ? 'light' : 'dark')
        : t;
      setResolvedTheme(effective);
      // GSAP fade transition for smooth theme switch
      root.style.transition = 'background-color 0.3s ease, color 0.3s ease';
      root.setAttribute('data-theme', effective);
      root.classList.toggle('dark', effective === 'dark');
      root.classList.toggle('light', effective === 'light');
    };

    apply(theme);

    const listener = () => { if (theme === 'system') apply('system'); };
    mq.addEventListener('change', listener);
    return () => mq.removeEventListener('change', listener);
  }, [theme]);

  const setTheme = (t: Theme) => {
    localStorage.setItem('svai-theme', t);
    setThemeState(t);
  };

  return (
    <ThemeContext.Provider value={{ theme, resolvedTheme, setTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

export const useTheme = () => useContext(ThemeContext);