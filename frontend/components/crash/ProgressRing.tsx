'use client';

// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
import React from 'react';

// frontend/components/crash/ProgressRing.tsx
// SVG ring that depletes as countdown progresses

import { useRef } from 'react';
import { useGSAP } from '@gsap/react';
import { gsap } from '@/lib/gsap';

interface ProgressRingProps {
  seconds: number;
  total?: number;
  size?: number;
}

export function ProgressRing({ seconds, total = 20, size = 100 }: ProgressRingProps) {
  const circleRef = useRef<SVGCircleElement>(null);
  const R = (size - 12) / 2;
  const circumference = 2 * Math.PI * R;
  const progress = seconds / total;
  const center = size / 2;

  useGSAP(() => {
    if (!circleRef.current) return;

    gsap.to(circleRef.current, {
      strokeDashoffset: circumference * (1 - progress),
      duration: 0.9,
      ease: 'none', // linear - countdown should be perfectly linear
    });

    // Color shifts red as time runs out
    if (seconds <= 5) {
      gsap.to(circleRef.current, {
        stroke: '#FF0000',
        duration: 0.3,
      });
    } else if (seconds <= 10) {
      gsap.to(circleRef.current, {
        stroke: '#FF6B6B',
        duration: 0.3,
      });
    }
  }, { dependencies: [seconds, circumference, progress], scope: circleRef });

  return (
    <svg
      width={size}
      height={size}
      style={{ transform: 'rotate(-90deg)' }}
      aria-label={`${seconds} seconds remaining`}
    >
      {/* Background ring */}
      <circle
        cx={center}
        cy={center}
        r={R}
        fill="none"
        stroke="rgba(255,255,255,0.15)"
        strokeWidth="4"
      />
      {/* Progress ring */}
      <circle
        ref={circleRef}
        className="progress-ring-circle"
        cx={center}
        cy={center}
        r={R}
        fill="none"
        stroke="white"
        strokeWidth="4"
        strokeLinecap="round"
        strokeDasharray={circumference}
        strokeDashoffset={0}
      />
    </svg>
  );
}