// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

'use client';

import { useState, useEffect, useCallback } from 'react';

interface SWUpdateHook {
  waitingSw: ServiceWorker | null;
  updateAvailable: boolean;
  applyUpdate: () => void;
  dismissUpdate: () => void;
}

export function useServiceWorkerUpdate(): SWUpdateHook {
  const [waitingSw, setWaitingSw] = useState<ServiceWorker | null>(null);
  const [dismissed, setDismissed] = useState(false);

  useEffect(() => {
    if (!('serviceWorker' in navigator)) return;

    const handleControllerChange = () => {
      navigator.serviceWorker.getRegistration().then(function (reg) {
        if (reg?.waiting) setWaitingSw(reg.waiting);
      });
    };

    navigator.serviceWorker.addEventListener('controllerchange', handleControllerChange);

    navigator.serviceWorker.getRegistration().then(function (reg) {
      if (reg?.waiting) {
        setWaitingSw(reg.waiting);
      }
      if (reg) {
        reg.addEventListener('updatefound', function () {
          var newWorker = reg.installing;
          if (newWorker) {
            newWorker.addEventListener('statechange', function () {
              if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                setWaitingSw(newWorker);
              }
            });
          }
        });
      }
    });

    return function () {
      navigator.serviceWorker.removeEventListener('controllerchange', handleControllerChange);
    };
  }, []);

  var applyUpdate = useCallback(function () {
    if (waitingSw) {
      waitingSw.postMessage({ action: 'SKIP_WAITING' });
      navigator.serviceWorker.addEventListener('controllerchange', function () {
        window.location.reload();
      });
    }
  }, [waitingSw]);

  var dismissUpdate = useCallback(function () {
    setDismissed(true);
    try {
      localStorage.setItem('pwa_update_dismissed', Date.now().toString());
    } catch {}
  }, []);

  useEffect(function () {
    try {
      var t = localStorage.getItem('pwa_update_dismissed');
      if (t) {
        if (Date.now() - parseInt(t, 10) < 86400000) {
          setDismissed(true);
        } else {
          localStorage.removeItem('pwa_update_dismissed');
        }
      }
    } catch {}
  }, []);

  return { waitingSw: waitingSw, updateAvailable: waitingSw !== null && !dismissed, applyUpdate: applyUpdate, dismissUpdate: dismissUpdate };
}
