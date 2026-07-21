'use client';

// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
import React from 'react';


import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { haptics } from '@/lib/haptics';
import { SOS_HIDDEN_ROUTES } from '@/lib/routes';

export function GlobalSOS() {
  const pathname = usePathname();

  if (SOS_HIDDEN_ROUTES.some((route) => {
    if (route === '/') return pathname === '/';
    return pathname === route || pathname.startsWith(route);
  })) return null;

  const handleClick = () => {
    haptics.heavy();
  };

  return (
    <>
      {/* Mobile SOS — positioned above BottomNav */}
      <div className="fixed bottom-[calc(7rem+env(safe-area-inset-bottom))] right-5 z-50 lg:hidden pointer-events-auto">
        <Link href="/sos" onClick={handleClick}>
          <button
            aria-label="Emergency SOS"
            className="w-14 h-14 bg-gradient-to-br from-emergency to-red-800 rounded-full flex items-center justify-center shadow-[0_0_30px_rgba(255,85,69,0.4)] text-white font-black text-sm tracking-widest relative overflow-hidden group"
          >
            <div
              className="absolute inset-0 rounded-full border-2 border-white/30"
            />
            <span className="relative z-10">SOS</span>
          </button>
        </Link>
      </div>

      {/* Desktop SOS */}
      <div className="fixed bottom-10 right-10 z-[60] hidden lg:block pointer-events-auto">
        <Link href="/sos" onClick={handleClick}>
          <button
            aria-label="Emergency SOS"
            className="w-20 h-20 bg-gradient-to-br from-emergency to-red-800 rounded-full flex items-center justify-center shadow-[0_0_50px_rgba(255,85,69,0.4)] text-white font-black tracking-tighter relative overflow-hidden group"
          >
            <div
              className="absolute inset-0 rounded-full border-4 border-white/20"
            />
            <span className="text-xl relative z-10 leading-none mb-0.5">SOS</span>
          </button>
        </Link>
      </div>
    </>
  );
}