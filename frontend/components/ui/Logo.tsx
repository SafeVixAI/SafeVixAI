'use client';

// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team


import React from 'react';

interface LogoProps {
  size?: number;
  status?: 'online' | 'offline' | 'emergency';
  interactive?: boolean;
  className?: string;
}

export function Logo({
  size = 40,
  status = 'online',
  interactive = true,
  className = '',
}: LogoProps) {
  // Color configuration based on status
  const getGradientColors = () => {
    switch (status) {
      case 'emergency':
        return {
          primary: '#FF3B30',
          secondary: '#FF9500',
          glow: 'rgba(255, 59, 48, 0.4)',
        };
      case 'offline':
        return {
          primary: '#9CA3AF',
          secondary: '#4B5563',
          glow: 'rgba(156, 163, 175, 0.2)',
        };
      case 'online':
      default:
        return {
          primary: '#00F2FE',
          secondary: '#4FACFE',
          glow: 'rgba(0, 242, 254, 0.4)',
        };
    }
  };

  const colors = getGradientColors();

  return (
    <div
      className={`relative select-none flex items-center justify-center ${
        interactive ? 'group cursor-pointer active:scale-95 transition-transform duration-300' : ''
      } ${className}`}
      style={{ width: size, height: size }}
    >
      {/* ── Interactive Ambient Backlight Glow ── */}
      {interactive && status !== 'offline' && (
        <div
          className="absolute inset-0 rounded-full blur-xl opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none scale-125"
          style={{
            background: `radial-gradient(circle, ${colors.primary} 0%, transparent 70%)`,
            mixBlendMode: 'screen',
          }}
        />
      )}

      {/* ── Vector SVG Logo (Road Safety + Vision AI Shield) ── */}
      <svg
        viewBox="0 0 100 100"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="w-full h-full relative z-10 overflow-visible"
      >
        <defs>
          {/* Main Gradient */}
          <linearGradient id={`logo-grad-${status}`} x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor={colors.primary} />
            <stop offset="100%" stopColor={colors.secondary} />
          </linearGradient>

          {/* Glow Filter */}
          <filter id={`logo-glow-${status}`} x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="3" result="blur" />
            <feComposite in="SourceGraphic" in2="blur" operator="over" />
          </filter>
        </defs>

        {/* ── 1. Outer Rotating Scanning Ring (AI Sentinel Active) ── */}
        <circle
          cx="50"
          cy="50"
          r="45"
          stroke={`url(#logo-grad-${status})`}
          strokeWidth="2"
          strokeLinecap="round"
          strokeDasharray="18 12 6 12"
          className={`origin-center ${
            status === 'emergency'
              ? 'animate-[spin_3s_linear_infinite]'
              : status === 'offline'
              ? ''
              : 'animate-[spin_12s_linear_infinite] group-hover:animate-[spin_4s_linear_infinite]'
          } transition-all duration-500`}
          opacity="0.8"
        />

        {/* ── 2. Protective Hexagonal Outer Shield Border ── */}
        <path
          d="M50 6 L86 26 L86 66 L50 94 L14 66 L14 26 Z"
          stroke={`url(#logo-grad-${status})`}
          strokeWidth="1.5"
          strokeLinejoin="round"
          opacity="0.25"
          className="transition-all duration-300 group-hover:opacity-60"
        />

        {/* ── 3. Protective Inner Shield Body (Glassmorphism fill) ── */}
        <path
          d="M50 12 L78 28 L78 62 L50 86 L22 62 L22 28 Z"
          fill={`url(#logo-grad-${status})`}
          fillOpacity="0.03"
          stroke={`url(#logo-grad-${status})`}
          strokeWidth="3.5"
          strokeLinejoin="round"
          filter={`url(#logo-glow-${status})`}
          className="transition-all duration-300 group-hover:fill-opacity-8"
        />

        {/* ── 4. Thematic Elements: AI Road Safety & Navigation ── */}
        
        {/* Converging Highway/Road Perspective Lines */}
        <path
          d="M32 82 L47 48 M68 82 L53 48"
          stroke={`url(#logo-grad-${status})`}
          strokeWidth="3"
          strokeLinecap="round"
          opacity="0.4"
          className="transition-all duration-300 group-hover:opacity-75"
        />

        {/* Lane Divider Lines (Pulsing / Moving illusion on hover) */}
        <path
          d="M50 78 L50 52"
          stroke={`url(#logo-grad-${status})`}
          strokeWidth="2"
          strokeLinecap="round"
          strokeDasharray="4 8"
          opacity="0.5"
          className="transition-all duration-300 group-hover:opacity-90 animate-[pulse_1.5s_infinite]"
        />

        {/* Computer Vision Aperture (Glowing central lens at the road's horizon) */}
        <circle
          cx="50"
          cy="42"
          r="10"
          fill="#071325"
          stroke={`url(#logo-grad-${status})`}
          strokeWidth="3"
          filter={`url(#logo-glow-${status})`}
          className="transition-all duration-300 group-hover:scale-110 origin-center"
        />

        {/* Optical Sensor Aperture Blades / Iris detail */}
        <circle
          cx="50"
          cy="42"
          r="4"
          fill={`url(#logo-grad-${status})`}
          className="animate-[pulse_2s_infinite]"
        />

        {/* Real-time Computer Vision Crosshair / GPS Target grid */}
        <path
          d="M36 42 L28 42 M64 42 L72 42 M50 28 L50 20"
          stroke={`url(#logo-grad-${status})`}
          strokeWidth="1.5"
          strokeLinecap="round"
          opacity="0.3"
          className="transition-all duration-300 group-hover:opacity-80"
        />

        {/* GPS Signal Radar pulses emitting from the central scanner */}
        <path
          d="M36 30 C42 24, 58 24, 64 30"
          stroke={`url(#logo-grad-${status})`}
          strokeWidth="1.5"
          strokeLinecap="round"
          opacity="0.25"
          className="animate-[pulse_2.5s_infinite_200ms] origin-center"
        />
      </svg>
    </div>
  );
}