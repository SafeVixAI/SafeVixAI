// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
import React from 'react';

import Link from 'next/link';
import { useRef } from 'react';
import { useVirtualizer } from '@tanstack/react-virtual';
import { Loader2, MapPin, Navigation, Phone, Search } from 'lucide-react';
import { gsap } from '@/lib/gsap';
import { useGSAP } from '@gsap/react';
import { ServiceIcon } from '../locator-components';
import { LocatorService, fallbackNumber } from '../locator-utils';

interface ResultsProps {
  filtered: LocatorService[];
  selectedServiceId: string | null;
  routeLoadingId: string | null;
  onLocateService: (_service: LocatorService) => void;
  onPreviewService: (_service: LocatorService) => void;
}

export function MobileResultsList({
  filtered,
  selectedServiceId,
  routeLoadingId,
  onLocateService,
  onPreviewService,
}: ResultsProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  useGSAP(() => {
    if (!containerRef.current) return;
    const cards = containerRef.current.querySelectorAll('.locator-result-card');
    if (cards.length > 0) {
      gsap.fromTo(cards,
        { opacity: 0, y: 15, scale: 0.98 },
        { opacity: 1, y: 0, scale: 1, duration: 0.35, stagger: 0.05, ease: 'power2.out', clearProps: 'all' }
      );
    }
  }, { scope: containerRef, dependencies: [filtered] });

  const rowVirtualizer = useVirtualizer({
    count: filtered.length,
    getScrollElement: () => containerRef.current,
    estimateSize: () => 190,
    overscan: 3,
  });

  return (
    <div ref={containerRef} className="overflow-y-auto px-4 -mx-4" style={{ maxHeight: 'calc(100dvh - 320px)' }}>
      <div
        style={{
          height: `${rowVirtualizer.getTotalSize()}px`,
          width: '100%',
          position: 'relative',
        }}
      >
        {rowVirtualizer.getVirtualItems().map((virtualRow) => {
          const service = filtered[virtualRow.index];
          return (
            <div
              key={virtualRow.key}
              style={{
                position: 'absolute',
                top: 0,
                left: 0,
                width: '100%',
                height: `${virtualRow.size}px`,
                transform: `translateY(${virtualRow.start}px)`,
                paddingBottom: '16px',
              }}
            >
              <div
                className={`locator-result-card group relative rounded-lg p-5 backdrop-blur-xl shadow-sm transition-all ${
                  selectedServiceId === service.id
                    ? 'border border-brand/30 bg-brand/90 dark:border-brand/40 dark:bg-surface-1/70'
                    : 'border border-border-md bg-white/80 dark:border-white/5 dark:bg-surface-2/40 hover:bg-white dark:hover:bg-surface-3/60'
                }`}
              >
                <div className="absolute left-0 top-0 bottom-0 w-1.5" style={{ backgroundColor: service.accentColor }} />

                <div className="flex justify-between items-start mb-5">
                  <div className="flex gap-4">
                    <div
                      className="w-12 h-12 rounded-xl flex items-center justify-center bg-surface-2 dark:bg-white/5 border border-border-md dark:border-white/10 shadow-inner"
                      style={{ color: service.accentColor }}
                    >
                      <ServiceIcon type={service.type} className="w-6 h-6" />
                    </div>
                    <div>
                      <h3 className="text-text-1 dark:text-text-1 font-black text-base tracking-tight font-space">
                        {service.name}
                      </h3>
                      <div className="flex items-center gap-1.5 mt-0.5">
                        <MapPin size={12} className="text-text-2" />
                        <span className="text-xs text-text-2 dark:text-text-2 font-bold">{service.address}</span>
                      </div>
                    </div>
                  </div>
                  <div className="bg-brand/[0.08] dark:bg-brand/10 px-3 py-1 rounded-lg border border-brand/20 dark:border-brand/20">
                    <span className="text-[10px] font-semibold text-brand dark:text-brand-light tracking-tight">
                      {service.distance}
                    </span>
                  </div>
                </div>

                <div className="flex gap-3">
                  <Link href={`tel:${service.phone ?? fallbackNumber(service.filterType)}`} className="flex-1">
                    <button className="w-full bg-brand-light hover:bg-brand text-white py-3.5 rounded-xl flex items-center justify-center gap-2 font-black text-[12px] uppercase tracking-widest transition-all active:scale-95 shadow-lg shadow-brand-light/20">
                      <Phone size={16} /> Call
                    </button>
                  </Link>
                  <button
                    type="button"
                    onClick={() => onLocateService(service)}
                    className="flex-1 bg-surface-2 dark:bg-white/5 border border-border-md dark:border-white/10 text-text-2 dark:text-text-3 py-3.5 rounded-xl flex items-center justify-center gap-2 font-black text-[12px] uppercase tracking-widest transition-all hover:bg-surface-2 dark:hover:bg-white/10 disabled:cursor-not-allowed disabled:opacity-70"
                    disabled={routeLoadingId === service.id}
                  >
                    {routeLoadingId === service.id ? (
                      <>
                        <Loader2 size={16} className="animate-spin" /> Routing
                      </>
                    ) : (
                      <>
                        <Navigation size={16} /> Locate
                      </>
                    )}
                  </button>
                  <button
                    type="button"
                    onClick={() => onPreviewService(service)}
                    className="flex-1 bg-surface-2 dark:bg-white/5 border border-border-md dark:border-white/10 text-text-2 dark:text-text-3 py-3.5 rounded-xl flex items-center justify-center gap-2 font-black text-[12px] uppercase tracking-widest transition-all hover:bg-surface-2 dark:hover:bg-white/10"
                  >
                    <Search size={16} /> Focus
                  </button>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export function DesktopResultsList({
  filtered,
  selectedServiceId,
  routeLoadingId,
  onLocateService,
  onPreviewService,
}: ResultsProps) {
  const parentRef = useRef<HTMLDivElement>(null);

  useGSAP(() => {
    if (!parentRef.current) return;
    const cards = parentRef.current.querySelectorAll('.locator-result-card');
    if (cards.length > 0) {
      gsap.fromTo(cards,
        { opacity: 0, y: 15, scale: 0.98 },
        { opacity: 1, y: 0, scale: 1, duration: 0.35, stagger: 0.05, ease: 'power2.out', clearProps: 'all' }
      );
    }
  }, { scope: parentRef, dependencies: [filtered] });

  const rowVirtualizer = useVirtualizer({
    count: filtered.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 180,
    overscan: 5,
  });

  return (
    <div ref={parentRef} className="flex-1 overflow-y-auto px-6 lg:px-8 py-4 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
      <div
        style={{
          height: `${rowVirtualizer.getTotalSize()}px`,
          width: '100%',
          position: 'relative',
        }}
      >
        {rowVirtualizer.getVirtualItems().map((virtualRow) => {
          const service = filtered[virtualRow.index];
          return (
            <div
              key={virtualRow.key}
              style={{
                position: 'absolute',
                top: 0,
                left: 0,
                width: '100%',
                height: `${virtualRow.size}px`,
                transform: `translateY(${virtualRow.start}px)`,
                paddingBottom: '16px',
              }}
            >
              <div
                className={`locator-result-card h-full group rounded-lg p-5 lg:p-6 transition-all ${
                  selectedServiceId === service.id
                    ? 'border border-brand/30 bg-brand/[0.08] dark:border-brand/40 dark:bg-surface-1/70'
                    : 'border border-border-md bg-surface-2 hover:bg-surface-2 dark:border-white/5 dark:bg-surface-1/40 dark:hover:bg-surface-2/60'
                }`}
              >
                <div className="flex justify-between items-start">
                  <div className="flex gap-4 lg:gap-5">
                    <div
                      className="w-12 h-12 lg:w-14 lg:h-14 rounded-lg shrink-0 flex items-center justify-center bg-white dark:bg-bg shadow-sm border border-border-md dark:border-white/10"
                      style={{ color: service.accentColor }}
                    >
                      <ServiceIcon type={service.type} className="w-6 h-6 lg:w-7 lg:h-7" />
                    </div>
                    <div className="overflow-hidden">
                      <span className="text-[8px] lg:text-[9px] font-semibold uppercase tracking-[0.1em] mb-1 block opacity-70" style={{ color: service.accentColor }}>
                        {service.type}
                      </span>
                      <h3 className="text-base lg:text-xl font-bold text-text-1 dark:text-[#dae6ff] truncate">{service.name}</h3>
                      <div className="flex items-center gap-3 mt-2">
                        <div className="flex items-center gap-1">
                          <Navigation size={12} className="text-text-2" />
                          <span className="text-[10px] lg:text-[11px] font-bold text-text-2 dark:text-text-2">
                            {service.distance}
                          </span>
                        </div>
                      </div>
                      <div className="mt-2 text-xs text-text-2 dark:text-text-2 line-clamp-2">{service.address}</div>
                    </div>
                  </div>
                </div>

                <div className="mt-6 flex gap-3">
                  <Link href={`tel:${service.phone ?? fallbackNumber(service.filterType)}`} className="flex-1">
                    <button className="w-full bg-brand-light hover:bg-brand text-white font-black py-2.5 rounded-xl text-[9px] lg:text-[10px] uppercase tracking-widest flex items-center justify-center gap-2 transition-all">
                      <Phone size={14} /> Call
                    </button>
                  </Link>
                  <button
                    type="button"
                    onClick={() => onLocateService(service)}
                    className="px-4 py-2.5 rounded-xl bg-brand text-white font-bold text-[9px] lg:text-[10px] uppercase tracking-widest hover:bg-brand/80 disabled:cursor-not-allowed disabled:opacity-70 flex items-center justify-center gap-2"
                    disabled={routeLoadingId === service.id}
                  >
                    {routeLoadingId === service.id ? (
                      <>
                        <Loader2 size={12} className="animate-spin" /> Routing
                      </>
                    ) : (
                      <>
                        <Navigation size={12} /> Locate
                      </>
                    )}
                  </button>
                  <button
                    type="button"
                    onClick={() => onPreviewService(service)}
                    className="px-4 py-2.5 rounded-xl border border-border-md dark:border-white/10 text-text-2 dark:text-text-2 font-bold text-[9px] lg:text-[10px] uppercase tracking-widest hover:bg-surface-2 dark:hover:bg-white/5"
                  >
                    Focus
                  </button>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
