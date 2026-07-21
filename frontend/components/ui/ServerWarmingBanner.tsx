'use client';

// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
import React from 'react';


import { useRef, useEffect, useState } from 'react';
import { useServerWarming } from '@/lib/store';
import { useGSAP } from '@gsap/react';
import { gsap } from '@/lib/gsap';
import { Loader2 } from 'lucide-react';
import { useTranslation } from 'react-i18next';

export function ServerWarmingBanner() {
  const { t } = useTranslation('common');
  const serverWarming = useServerWarming();
  const bannerRef = useRef<HTMLDivElement>(null);
  const [shouldRender, setShouldRender] = useState(serverWarming);

  useEffect(() => {
    if (serverWarming) {
      setShouldRender(true);
    }
  }, [serverWarming]);

  useGSAP(() => {
    if (!bannerRef.current) return;
    if (serverWarming) {
      // Slide up
      gsap.fromTo(
        bannerRef.current,
        { y: 80, opacity: 0 },
        { y: 0, opacity: 1, duration: 0.4, ease: 'power2.out' }
      );
    } else {
      // Slide down and unmount
      gsap.to(bannerRef.current, {
        y: 80,
        opacity: 0,
        duration: 0.3,
        ease: 'power2.in',
        onComplete: () => setShouldRender(false),
      });
    }
  }, { dependencies: [serverWarming] });

  if (!shouldRender) return null;

  return (
    <div
      ref={bannerRef}
      className="fixed bottom-[80px] md:bottom-[24px] left-1/2 -translate-x-1/2 z-[999] bg-[var(--surface-4)] border border-[var(--border-md)] text-[var(--text-1)] text-xs font-semibold px-5 py-3 rounded-full flex items-center gap-2.5 shadow-2xl backdrop-blur-md"
      role="status"
      aria-live="polite"
    >
      <Loader2 size={14} className="animate-spin text-brand-light shrink-0" />
      <span>{t('connecting_server', 'Connecting... (~30 seconds on first load)')}</span>
    </div>
  );
}