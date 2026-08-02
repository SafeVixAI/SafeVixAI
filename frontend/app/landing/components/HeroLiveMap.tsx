// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

'use client';

import React from 'react';

/**
 * SafeVixAI Landing — Abstract SVG Grid Graphic
 * Replaces MapLibre to improve performance and avoid network/rendering issues.
 */
export default function HeroLiveMap() {
  return (
    <div className="w-full h-full relative rounded-lg overflow-hidden bg-brand-darkest border border-brand/20 flex flex-col items-center justify-center" style={{ minHeight: '600px' }}>
      
      {/* Background glow */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-3/4 h-3/4 bg-brand-primary/10 blur-[100px] rounded-full pointer-events-none" />

      {/* Abstract Tech SVG Grid */}
      <svg className="absolute inset-0 w-full h-full opacity-30" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <pattern id="gridPattern" width="40" height="40" patternUnits="userSpaceOnUse">
            <path d="M 40 0 L 0 0 0 40" fill="none" stroke="currentColor" strokeWidth="1" className="text-brand-primary/20" />
            <circle cx="40" cy="40" r="1.5" className="fill-brand-light/50" />
          </pattern>
          <linearGradient id="glowLine" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="transparent" />
            <stop offset="50%" stopColor="#10b981" />
            <stop offset="100%" stopColor="transparent" />
          </linearGradient>
        </defs>
        <rect width="100%" height="100%" fill="url(#gridPattern)" />
        
        {/* Animated scanning line */}
        <line x1="0" y1="20%" x2="100%" y2="20%" stroke="url(#glowLine)" strokeWidth="2" opacity="0.8">
          <animate attributeName="y1" values="0%;100%;0%" dur="10s" repeatCount="indefinite" />
          <animate attributeName="y2" values="0%;100%;0%" dur="10s" repeatCount="indefinite" />
        </line>
      </svg>

      {/* Nodes / Pulses */}
      <div className="absolute top-[30%] left-[20%]">
        <div className="w-3 h-3 rounded-full bg-brand-light animate-pulse shadow-[0_0_15px_#10b981]" />
        <div className="w-12 h-12 rounded-full border border-brand-primary absolute -top-[18px] -left-[18px] animate-ping opacity-20" />
      </div>
      <div className="absolute top-[60%] left-[70%]">
        <div className="w-4 h-4 rounded-full bg-brand-primary animate-pulse shadow-[0_0_20px_#10b981]" />
        <div className="w-16 h-16 rounded-full border border-brand-primary absolute -top-[24px] -left-[24px] animate-ping opacity-20 delay-700" />
      </div>
      <div className="absolute top-[40%] left-[50%]">
        <div className="w-2 h-2 rounded-full bg-amber-400 animate-pulse shadow-[0_0_10px_#fbbf24]" />
        <div className="w-8 h-8 rounded-full border border-amber-400 absolute -top-[12px] -left-[12px] animate-ping opacity-20 delay-300" />
      </div>

      <div className="relative z-10 flex flex-col items-center justify-center text-center p-8 bg-brand-darkest/60 backdrop-blur-md border border-brand/20 rounded-xl">
        <div className="w-12 h-12 mb-4 rounded-full border-2 border-brand-primary/50 flex items-center justify-center">
          <svg className="w-6 h-6 text-brand-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
        </div>
        <h3 className="text-xl font-bold text-white font-display tracking-wide mb-2">INTELLIGENCE NETWORK ONLINE</h3>
        <p className="text-sm font-mono text-brand-light/70 uppercase tracking-widest">
          Spatial analysis grid active.
        </p>
      </div>

    </div>
  );
}
