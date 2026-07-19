// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
import React from 'react';

'use client';

import { useRef, useState, useEffect } from 'react';
import { useOnlineStatus } from '@/hooks/useOnlineStatus';
import { WifiOff } from 'lucide-react';
import { useGSAP } from '@gsap/react';
import { gsap } from '@/lib/gsap';
import { useTranslation } from 'react-i18next';

export function OfflineBanner() {
  const isOnline = useOnlineStatus();
  const bannerRef = useRef<HTMLDivElement>(null);
  const [shouldRender, setShouldRender] = useState(!isOnline);
  const { t } = useTranslation('common');

  useEffect(() => {
    if (!isOnline) {
      setShouldRender(true);
    }
  }, [isOnline]);

  useGSAP(() => {
    if (!bannerRef.current) return;
    if (!isOnline) {
      // Slide down
      gsap.fromTo(
        bannerRef.current,
        { y: -50, opacity: 0 },
        { y: 0, opacity: 1, duration: 0.4, ease: 'power2.out' }
      );
    } else {
      // Slide up and then unmount
      gsap.to(bannerRef.current, {
        y: -50,
        opacity: 0,
        duration: 0.3,
        ease: 'power2.in',
        onComplete: () => setShouldRender(false),
      });
    }
  }, { dependencies: [isOnline] });

  if (!shouldRender) return null;

  return (
    <div
      ref={bannerRef}
      className="fixed top-0 left-0 right-0 z-[999] bg-brand text-white text-xs font-semibold px-4 py-2 flex items-center justify-center gap-2 shadow-md border-b border-brand-light/20"
      role="alert"
      aria-live="assertive"
    >
      <WifiOff size={14} className="shrink-0 text-brand-light animate-pulse" />
      <span>{t('common.offline_banner_text', 'Offline — Emergency locator, First Aid & SOS still work')}</span>
    </div>
  );
}
