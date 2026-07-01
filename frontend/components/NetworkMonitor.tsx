// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

'use client';

import { useEffect } from 'react';
import { useAppStore } from '@/lib/store';
import { useShallow } from 'zustand/react/shallow';

export function NetworkMonitor() {
  const { setConnectivity } = useAppStore(useShallow((s) => ({ setConnectivity: s.setConnectivity })));

  useEffect(() => {
    // Initial check
    /* istanbul ignore if */
    if (typeof navigator !== 'undefined') {
      setConnectivity(navigator.onLine ? 'online' : 'offline');
    }

    const handleOnline = () => {
/* istanbul ignore next */
      // In a real app we might ping a server to verify. For now, trust the browser.
      /* istanbul ignore next */
      setConnectivity('online');
    };
/* istanbul ignore next */

    const handleOffline = () => {
      /* istanbul ignore next */
      setConnectivity('offline');
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, [setConnectivity]);

  return null;
}
