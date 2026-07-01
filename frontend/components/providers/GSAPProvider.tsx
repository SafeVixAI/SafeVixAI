// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

// frontend/components/providers/GSAPProvider.tsx
'use client';

import { useEffect, useRef } from 'react';
import { usePathname } from 'next/navigation';

// Routes that have GSAP animations â€” everything else skips the 50KB GSAP bundle
const ANIMATION_ROUTES = new Set([
  '/', '/assistant', '/bystander', '/challan', '/command-center',
  '/emergency', '/first-aid', '/guide', '/landing', '/locator',
  '/officer', '/report', '/report/track', '/sos', '/tracking',
]);

function needsAnimation(pathname: string): boolean {
  for (const route of ANIMATION_ROUTES) {
/* istanbul ignore next */
    if (pathname === route || pathname.startsWith(route + '/')) return true;
    /* istanbul ignore next */
    if (route.includes('[session_id]') && pathname.startsWith('/track/')) return true;
  }
  /* istanbul ignore next */
  return false;
}

export function GSAPProvider({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const gsapRef = useRef<{ gsap: typeof import('gsap')['gsap']; ScrollTrigger: typeof import('gsap/ScrollTrigger')['ScrollTrigger'] } | null>(null);

  // Trigger GSAP module import (registers plugins at module scope) only on animated routes
  useEffect(() => {
    if (!needsAnimation(pathname)) return;
    let cancelled = false;
    import('@/lib/gsap').then((mod) => {
      if (cancelled) return;
      gsapRef.current = mod;
    });
    return () => { cancelled = true; };
  }, [pathname]);

  // Kill animations on route change
  useEffect(() => {
    if (!needsAnimation(pathname)) return;
    return () => {
      import('@/lib/gsap').then(({ gsap, ScrollTrigger }) => {
        ScrollTrigger.getAll().forEach((t) => t.kill());
        gsap.killTweensOf('*');
      });
    };
  }, [pathname]);

  // Respect prefers-reduced-motion
  useEffect(() => {
    if (!needsAnimation(pathname)) return;
    const mq = window.matchMedia('(prefers-reduced-motion: reduce)');
    /* istanbul ignore next */
    if (mq.matches && gsapRef.current) {
      gsapRef.current.gsap.globalTimeline.timeScale(1000);
    }
    const handler = (e: MediaQueryListEvent) => {
      /* istanbul ignore next */
      if (gsapRef.current) {
        gsapRef.current.gsap.globalTimeline.timeScale(e.matches ? 1000 : 1);
      }
    };
    mq.addEventListener('change', handler);
    return () => mq.removeEventListener('change', handler);
  }, [pathname]);

  return <>{children}</>;
}
