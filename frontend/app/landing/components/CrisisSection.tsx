// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
import React from 'react';

'use client';


import { useScrollReveal, useCountUp } from '../hooks/useLandingGSAP';

/* ═══════════════════════════════════════════════════════
   Crisis Metric Card — individual animated counter card
   ═══════════════════════════════════════════════════════ */

interface MetricCardProps {
  value: string;
  numericValue: number;
  suffix: string;
  label: string;
  color: string;
}

function MetricCard({ numericValue, suffix, label, color }: MetricCardProps) {
  const counterRef = useCountUp(numericValue, { duration: 2.5, start: 'top 80%' });

  return (
    <div className="reveal-item bg-surface-1 border border-white/[0.06] rounded-xl p-8 text-center group hover:border-white/[0.12] transition-colors duration-300">
      <div
        className="counter-number text-[clamp(2.5rem,5vw,4rem)] font-extrabold leading-none"
        style={{ color }}
      >
        <span ref={counterRef}>0</span>
        {suffix && (
          <span className="inline-block">{suffix}</span>
        )}
      </div>
      <p className="text-sm text-text-2 mt-3 uppercase tracking-wider font-medium">
        {label}
      </p>
      {/* Subtle bottom accent bar */}
      <div
        className="mt-6 mx-auto h-[2px] w-12 rounded-full opacity-30 group-hover:opacity-60 group-hover:w-16 transition-all duration-500"
        style={{ backgroundColor: color }}
      />
    </div>
  );
}

/* ═══════════════════════════════════════════════════════
   CRISIS METRICS DATA
   ═══════════════════════════════════════════════════════ */

interface CrisisMetric {
  value: string;
  numericValue: number;
  suffix: string;
  label: string;
  color: string;
}

const CRISIS_METRICS: CrisisMetric[] = [
  {
    value: '4,61,312',
    numericValue: 461312,
    suffix: '',
    label: 'Road Accidents Annually',
    color: '#DC2626',
  },
  {
    value: '1,72,027',
    numericValue: 172027,
    suffix: '',
    label: 'Lives Lost Every Year',
    color: '#DC2626',
  },
  {
    value: '50%',
    numericValue: 50,
    suffix: '%',
    label: 'Die Within First Hour',
    color: '#D97706',
  },
  {
    value: '11,00,000+',
    numericValue: 1100000,
    suffix: '+',
    label: 'Hazard Reports Unresolved',
    color: '#3B82F6',
  },
];

/* ═══════════════════════════════════════════════════════
   CrisisSection — Emotional national road safety crisis
   ═══════════════════════════════════════════════════════ */

export default function CrisisSection() {
  const containerRef = useScrollReveal({ y: 50, duration: 0.9, stagger: 0.12 });

  return (
    <section
      id="crisis"
      className="landing-section bg-bg glow-emergency-ambient"
    >
      <div ref={containerRef} className="landing-container text-center relative z-[1]">
        {/* ── Overline ── */}
        <p className="reveal-item font-mono text-[11px] font-semibold tracking-[0.10em] uppercase text-emergency mb-4">
          The Crisis
        </p>

        {/* ── Subtitle ── */}
        <p className="reveal-item font-space text-lg text-text-2 mb-16">
          India&apos;s roads are the deadliest in the world.
        </p>

        {/* ── Metrics Grid ── */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 lg:gap-8">
          {CRISIS_METRICS.map((metric) => (
            <MetricCard
              key={metric.label}
              value={metric.value}
              numericValue={metric.numericValue}
              suffix={metric.suffix}
              label={metric.label}
              color={metric.color}
            />
          ))}
        </div>

        {/* ── Closing Statement ── */}
        <p className="reveal-item mt-16 font-space text-[clamp(1.25rem,3vw,2rem)] text-text-2 max-w-3xl mx-auto leading-relaxed">
          Every <span className="text-emergency font-semibold">4 minutes</span>, someone dies on Indian roads.
        </p>
      </div>
    </section>
  );
}
