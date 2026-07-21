'use client';

// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
import React from 'react';


import { Crosshair, Cpu, Scan, ShieldAlert } from 'lucide-react';
import Image from 'next/image';

interface HazardViewfinderProps {
  imageSrc?: string;
  isDetecting?: boolean;
  confidence?: number;
  statusLabel?: string;
  signalLabel?: string;
  locationLabel?: string;
  viewportId?: string;
}

export default function HazardViewfinder({
  imageSrc,
  isDetecting = true,
  confidence = 98.4,
  statusLabel = 'Live hazard viewport',
  signalLabel = 'Awaiting GPS',
  locationLabel = 'Awaiting live coordinates',
  viewportId = 'RW-LIVE-VIEWPORT',
}: HazardViewfinderProps) {
  return (
    <div className="relative h-full w-full overflow-hidden rounded-lg border border-white/5 bg-surface-1 shadow-2xl group">
      <div className="absolute inset-0 z-0">
        {imageSrc ? (
          <Image alt="Hazard evidence" src={imageSrc} fill className="object-cover opacity-60 grayscale mix-blend-luminosity transition-all duration-700 group-hover:grayscale-0" unoptimized />
        ) : (
          <div className="flex h-full w-full flex-col items-center justify-center gap-6 bg-bg/50">
            <div className="relative">
              <div className="h-32 w-32 rounded-full border border-emergency/20" />
              <div className="absolute inset-0 flex items-center justify-center">
                <Scan className="text-emergency/20" size={60} strokeWidth={0.5} />
              </div>
            </div>
            <div className="flex flex-col items-center gap-2 text-center">
              <span className="animate-pulse font-space text-[10px] font-semibold uppercase tracking-[0.4em] text-emergency/40">Camera uplink waiting</span>
              <span className="font-mono text-[8px] font-bold uppercase tracking-widest text-text-2">Add a real road photo for faster authority verification</span>
            </div>
          </div>
        )}
        <div className="absolute inset-0 z-10 bg-gradient-to-t from-bg via-transparent to-bg/40" />
      </div>

      <div className="pointer-events-none absolute inset-0 z-20 flex flex-col justify-between p-6">
        <div className="flex items-start justify-between">
          <div className="flex flex-col gap-1">
            <div className="flex items-center gap-2 rounded-lg border border-white/10 bg-black/60 px-3 py-1.5 backdrop-blur-md">
              <span className="h-1.5 w-1.5 rounded-full bg-emergency animate-pulse" />
              <span className="font-space text-[10px] font-semibold uppercase tracking-[0.1em] text-white">{statusLabel}</span>
            </div>
            <span className="pl-1 font-mono text-[9px] font-bold uppercase tracking-tight text-text-2">Vector: {locationLabel}</span>
          </div>

          <div className="flex flex-col items-end gap-1">
            <div className="flex items-center gap-2 rounded-lg border border-brand/20 bg-brand/10 px-3 py-1.5 backdrop-blur-md">
              <Cpu size={12} className="text-brand" />
              <span className="font-space text-[10px] font-semibold uppercase tracking-widest text-brand">AI Core {confidence}%</span>
            </div>
            <span className="font-mono text-[9px] font-bold uppercase tracking-tight text-text-2">Signal: {signalLabel}</span>
          </div>
        </div>

        <div className="absolute inset-0 flex items-center justify-center p-12">
          <div className="relative h-full w-full max-h-[280px] max-w-[280px]">
            <div className="absolute left-0 top-0 h-8 w-8 border-l-2 border-t-2 border-emergency/60" />
            <div className="absolute right-0 top-0 h-8 w-8 border-r-2 border-t-2 border-emergency/60" />
            <div className="absolute bottom-0 left-0 h-8 w-8 border-b-2 border-l-2 border-emergency/60" />
            <div className="absolute bottom-0 right-0 h-8 w-8 border-b-2 border-r-2 border-emergency/60" />

            {isDetecting ? <div className="absolute left-0 z-30 h-0.5 w-full bg-gradient-to-r from-transparent via-emergency to-transparent shadow-[0_0_15px_var(--emergency)]" /> : null}

            <div className="absolute inset-0 flex items-center justify-center opacity-20">
              <div className="h-full w-full rounded-full border border-emergency/80" />
              <div className="absolute h-2/3 w-2/3 rounded-full border border-emergency/80" />
            </div>

            <div className="absolute inset-0 flex items-center justify-center">
              <Crosshair className="text-emergency/40" size={40} strokeWidth={1} />
            </div>
          </div>
        </div>

        <div className="flex flex-col gap-1.5 self-start">
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 rounded-md bg-emergency px-3 py-1 shadow-lg shadow-emergency/20">
              <ShieldAlert size={12} className="text-white" />
              <span className="font-space text-[10px] font-semibold uppercase tracking-widest text-white">Confirmed hazard</span>
            </div>
            <div className="rounded-md border border-emergency/20 bg-emergency/10 px-2 py-1 text-[10px] font-bold uppercase tracking-widest text-emergency">
              {isDetecting ? 'Analyzing risk...' : 'Ready to dispatch'}
            </div>
          </div>
          <span className="pl-1 font-space text-[9px] font-semibold uppercase tracking-[0.1em] text-text-2 opacity-70">{viewportId}</span>
        </div>
      </div>

      {/* Spots removed per user request */}
    </div>
  );
}