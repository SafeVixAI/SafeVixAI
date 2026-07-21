'use client';

// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team


import React from 'react';
import { Droplet, Car, PhoneCall, Zap } from 'lucide-react';
import { useAppStore } from '@/lib/store';

export default function ProfileCard() {
  const userProfile = useAppStore((state) => state.userProfile);
  const displayName = userProfile.name || 'Emergency Profile';
  const initials = displayName
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join('') || 'SV';

  return (
    <div className="relative p-8 rounded-[2.5rem] bg-white dark:bg-white/5 border border-border-md dark:border-white/10 shadow-xl overflow-hidden group">
      <div className="flex flex-col items-center gap-6 relative z-10">
        <div className="relative group/avatar">
          <div className="w-24 h-24 rounded-full border-4 border-border-md dark:border-white/10 ring-4 ring-brand-light/ overflow-hidden relative bg-brand text-brand-light flex items-center justify-center">
            <span className="text-3xl font-black tracking-tight font-space">{initials}</span>
          </div>
          <button aria-label="Emergency profile status" className="absolute bottom-0 right-0 bg-brand-light p-2 rounded-full shadow-lg border-2 border-white dark:border-bg active:scale-90 transition-all">
            <Zap size={14} className="text-white" />
          </button>
        </div>

        <div className="text-center">
          <h3 className="text-2xl font-black text-text-1 dark:text-white tracking-tight uppercase font-space">{displayName}</h3>
          <p className="text-[10px] font-bold text-text-2 uppercase tracking-widest mt-1">
            {userProfile.name ? 'Verified emergency profile' : 'Complete profile for faster SOS dispatch'}
          </p>
        </div>
        
        <div className="w-full grid grid-cols-1 sm:grid-cols-3 gap-3">
          <div className="flex flex-col items-center gap-1 p-3 rounded-lg bg-surface-2 dark:bg-white/5 border border-border-md dark:border-white/5 shadow-sm">
            <Droplet size={14} className="text-red-500" />
            <span className="text-[9px] font-semibold uppercase text-text-2">{userProfile.bloodGroup || 'Blood group'}</span>
          </div>
          <div className="flex flex-col items-center gap-1 p-3 rounded-lg bg-surface-2 dark:bg-white/5 border border-border-md dark:border-white/5 shadow-sm">
            <Car size={14} className="text-brand-light" />
            <span className="text-[9px] font-semibold uppercase text-text-2">{userProfile.vehicleNumber || 'Vehicle ID'}</span>
          </div>
          <div className="flex flex-col items-center gap-1 p-3 rounded-lg bg-surface-2 dark:bg-white/5 border border-border-md dark:border-white/5 shadow-sm">
            <PhoneCall size={14} className="text-text-2" />
            <span className="text-[9px] font-semibold uppercase text-text-2">{userProfile.emergencyContact || 'Emergency contact'}</span>
          </div>
        </div>
      </div>
    </div>
  );
}