'use client';

// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team


import { useEffect, ReactNode } from 'react';
import { useAppStore } from '@/lib/store';
import { useShallow } from 'zustand/react/shallow';

export function ConnectivityProvider({ children }: { children: ReactNode }) {
  const { setConnectivity } = useAppStore(useShallow((s) => ({ setConnectivity: s.setConnectivity })));

  useEffect(() => {
    const update = () => {
/* istanbul ignore next */
      setConnectivity(navigator.onLine ? 'online' : 'offline');
    };

    // Set initial state
    setConnectivity(navigator.onLine ? 'online' : 'offline');

    window.addEventListener('online', update);
    window.addEventListener('offline', update);
    return () => {
      window.removeEventListener('online', update);
      window.removeEventListener('offline', update);
    };
  }, [setConnectivity]);

  return <>{children}</>;
}