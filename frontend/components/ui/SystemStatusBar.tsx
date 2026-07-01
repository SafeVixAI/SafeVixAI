// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

'use client';

import { useEffect, useState, useRef } from 'react';
import { X } from 'lucide-react';
import { useGSAP } from '@gsap/react';
import { gsap } from '@/lib/gsap';
import { PUBLIC_API_BASE_URL, PUBLIC_CHATBOT_BASE_URL } from '@/lib/public-env';

export function SystemStatusBar() {
  const [status, setStatus] = useState<'OPERATIONAL' | 'DEGRADED' | 'DOWN'>('OPERATIONAL');
  const [message, setMessage] = useState('');
  const [isDismissed, setIsDismissed] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const [shouldRender, setShouldRender] = useState(false);

  useEffect(() => {
    /* istanbul ignore next */
    if (typeof window !== 'undefined') {
      const dismissed = sessionStorage.getItem('svai-status-dismissed') === 'true' ||
                        (process.env.NODE_ENV !== 'production' && localStorage.getItem('__E2E_SKIP_AUTH__') === 'true');
      setIsDismissed(dismissed);
    }

    const checkHealth = async () => {
      try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 8000);
        
        const [backend, chatbot] = await Promise.allSettled([
          fetch(`${PUBLIC_API_BASE_URL}/health`, { signal: controller.signal, cache: 'no-store' }),
          fetch(`${PUBLIC_CHATBOT_BASE_URL}/health`, { signal: controller.signal, cache: 'no-store' }),
        ]);
        clearTimeout(timeoutId);

/* istanbul ignore next */
        const backendOk = backend.status === 'fulfilled' && backend.value.ok;
        const chatbotOk = chatbot.status === 'fulfilled' && chatbot.value.ok;

        if (backendOk && chatbotOk) {
          setStatus('OPERATIONAL');
          setMessage('');
        } else if (backendOk || chatbotOk) {
          setStatus('DEGRADED');
          setMessage('One SafeVixAI service is waking up. Core safety features remain available.');
        } else {
          setStatus('DOWN');
          setMessage('SafeVixAI services are waking up. Offline emergency tools remain available.');
        }
      /* istanbul ignore next */
      } catch {
/* istanbul ignore next */
        setStatus('DOWN');
/* istanbul ignore next */
        setMessage('SafeVixAI services are waking up. Offline emergency tools remain available.');
      }
    };

    checkHealth();
    const interval = setInterval(checkHealth, 60000);
    return () => clearInterval(interval);
  }, []);

  const active = status !== 'OPERATIONAL' && !isDismissed;

  useEffect(() => {
    if (active) {
      setShouldRender(true);
    }
  }, [active]);

  useGSAP(() => {
    /* istanbul ignore next */
    if (!containerRef.current) return;
    if (active) {
      /* istanbul ignore next */
      gsap.fromTo(
        containerRef.current,
        { y: -50, opacity: 0 },
        { y: 0, opacity: 1, duration: 0.4, ease: 'power2.out' }
      );
    } else {
      /* istanbul ignore next */
      gsap.to(containerRef.current, {
        y: -50,
        opacity: 0,
        duration: 0.3,
        ease: 'power2.in',
        onComplete: () => setShouldRender(false),
      });
    }
  }, { dependencies: [active] });

  const handleDismiss = () => {
    if (typeof window !== 'undefined') {
      sessionStorage.setItem('svai-status-dismissed', 'true');
    }
    setIsDismissed(true);
  };

  if (!shouldRender) return null;

  return (
    <div
      ref={containerRef}
      className={`fixed top-0 left-0 right-0 z-[1000] px-4 py-2 text-center text-xs font-bold shadow-md flex items-center justify-between transition-all ${
        status === 'DOWN'
          ? 'bg-red-500 text-white dark:bg-red-950 dark:text-red-200'
          : 'bg-brand text-white dark:bg-brand-light/10 dark:text-brand-light'
      }`}
      role="status"
      aria-live="polite"
    >
      <div className="flex-1 flex items-center justify-center gap-2">
        <span aria-hidden="true">{status === 'DOWN' ? '!' : 'i'}</span>
        <span>{message}</span>
      </div>
      <button
        onClick={handleDismiss}
        className="p-1 rounded-full hover:bg-black/10 dark:hover:bg-white/10 text-white dark:text-inherit transition-colors"
        aria-label="Dismiss System Status"
      >
        <X size={14} />
      </button>
    </div>
  );
}
