'use client';

// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team


import React, { memo, useRef } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { MapPin, BotMessageSquare, MapPinPlus, AlertTriangle, HeartPulse } from 'lucide-react';
import { useGSAP } from '@gsap/react';
import { gsap } from '@/lib/gsap';

interface NavItem {
  id: number;
  icon: React.ReactNode;
  label: string;
  href: string;
  accentColor: string;
}

const items: NavItem[] = [
  { id: 0, icon: <MapPin size={22} strokeWidth={2.5} />, label: "Map", href: "/", accentColor: 'var(--brand-light)' },
  { id: 1, icon: <BotMessageSquare size={22} strokeWidth={2.5} />, label: "AI Chat", href: "/assistant", accentColor: 'var(--brand)' },
  { id: 2, icon: <MapPinPlus size={22} strokeWidth={2.5} />, label: "Locator", href: "/locator", accentColor: 'var(--text-2)' },
  { id: 3, icon: <AlertTriangle size={22} strokeWidth={2.5} />, label: "Report", href: "/report", accentColor: 'var(--warning)' },
  { id: 4, icon: <HeartPulse size={22} strokeWidth={2.5} />, label: "First Aid", href: "/first-aid", accentColor: 'var(--emergency)' },
];

const BottomNav = memo(function BottomNav() {
  const pathname = usePathname();
  const indicatorRef = useRef<HTMLDivElement>(null);
  const navRef = useRef<HTMLDivElement>(null);

  const activeIndex = items.findIndex(item => item.href === pathname);
  const active = activeIndex !== -1 ? activeIndex : 0;
  const activeItem = items[active];

  // Animate indicator slide with GSAP spring
  useGSAP(() => {
    if (!indicatorRef.current) return;
    const itemWidth = 100 / items.length;
    const targetX = active * itemWidth + itemWidth / 2;
    gsap.to(indicatorRef.current, {
      x: `${targetX}vw`,
      duration: 0.4,
      ease: 'elastic.out(1, 0.75)',
    });
  }, { dependencies: [active] });

  // Entry animation
  useGSAP(() => {
    if (!navRef.current) return;
    gsap.fromTo(navRef.current,
      { y: 80, opacity: 0 },
      { y: 0, opacity: 1, duration: 0.5, ease: 'power3.out', delay: 0.2 }
    );
  }, { scope: navRef });

  return (
    <nav className="fixed bottom-0 left-0 z-[100] pointer-events-none w-full lg:hidden [@media(max-height:500px)]:hidden" aria-label="Main navigation">
      <div
        ref={navRef}
        className="relative flex items-center justify-around w-full pb-[env(safe-area-inset-bottom)] pt-2 overflow-hidden pointer-events-auto"
        style={{
          background: 'linear-gradient(to top, rgba(10,14,20,0.98) 0%, rgba(10,14,20,0.92) 60%, rgba(10,14,20,0.85) 100%)',
          backdropFilter: 'blur(20px) saturate(1.5)',
          WebkitBackdropFilter: 'blur(20px) saturate(1.5)',
          borderTop: '1px solid rgba(255,255,255,0.06)',
          boxShadow: '0 -8px 32px rgba(0,0,0,0.4), 0 -2px 8px rgba(0,0,0,0.2), inset 0 1px 0 rgba(255,255,255,0.04)',
        }}
      >
        {/* Active Indicator — Glowing dot + gradient beam */}
        <div
          ref={indicatorRef}
          className="absolute -z-10 transition-colors duration-300"
          style={{
            left: 0,
            transform: 'translateX(-50%)',
            top: '-1px',
          }}
        >
          {/* Top edge glow line */}
          <div
            className="w-12 h-[2px] rounded-full mx-auto"
            style={{
              background: `linear-gradient(90deg, transparent, ${activeItem.accentColor}, transparent)`,
              boxShadow: `0 0 12px ${activeItem.accentColor}`,
            }}
          />
          {/* Diffuse underglow */}
          <div
            className="w-16 h-16 rounded-full mx-auto -mt-4 blur-2xl opacity-20"
            style={{ backgroundColor: activeItem.accentColor }}
          />
        </div>

        {items.map((item, index) => {
          const isActive = index === active;
          return (
            <Link
              href={item.href}
              key={item.id}
              className="relative flex flex-col items-center group p-1 min-w-[56px] min-h-[52px]"
              aria-current={isActive ? "page" : undefined}
              onClick={() => {
                if (typeof window !== 'undefined' && navigator.vibrate) {
                  navigator.vibrate(8);
                }
              }}
            >
              {/* Icon container with scale + color transition */}
              <div
                className={`flex items-center justify-center w-9 h-9 rounded-xl relative z-10 transition-all duration-300 ${
                  isActive
                    ? 'scale-110'
                    : 'text-[#6B7A8D] group-hover:text-[#A8B4C4] scale-100'
                }`}
                style={isActive ? { color: activeItem.accentColor } : undefined}
              >
                {item.icon}

                {/* Active pip indicator */}
                {isActive && (
                  <span
                    className="absolute -bottom-0.5 w-1 h-1 rounded-full"
                    style={{
                      backgroundColor: activeItem.accentColor,
                      boxShadow: `0 0 6px ${activeItem.accentColor}`,
                    }}
                  />
                )}
              </div>

              {/* Label */}
              <span
                className={`text-[8px] font-bold mt-0.5 tracking-[0.08em] uppercase transition-all duration-300 ${
                  isActive
                    ? 'opacity-100 translate-y-0'
                    : 'text-[#4A5568] opacity-70 translate-y-0'
                }`}
                style={isActive ? { color: activeItem.accentColor } : undefined}
              >
                {item.label}
              </span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
});

export default BottomNav;