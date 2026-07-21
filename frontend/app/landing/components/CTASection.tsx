'use client';

// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
import React from 'react';


import Link from 'next/link';
import { ExternalLink } from 'lucide-react';
import { useScrollReveal } from '../hooks/useLandingGSAP';

/* ── Particle dot positions — pre-generated for determinism ── */
const PARTICLE_DOTS: { x: number; y: number; delay: number; size: number }[] = [
  { x: 5, y: 12, delay: 0, size: 4 },
  { x: 92, y: 8, delay: 1.2, size: 4 },
  { x: 18, y: 78, delay: 2.4, size: 4 },
  { x: 85, y: 72, delay: 0.6, size: 4 },
  { x: 42, y: 5, delay: 1.8, size: 4 },
  { x: 65, y: 88, delay: 3.0, size: 4 },
  { x: 10, y: 45, delay: 0.3, size: 4 },
  { x: 78, y: 38, delay: 2.1, size: 4 },
  { x: 30, y: 92, delay: 1.5, size: 4 },
  { x: 55, y: 15, delay: 0.9, size: 4 },
  { x: 8, y: 28, delay: 3.6, size: 4 },
  { x: 95, y: 55, delay: 2.7, size: 4 },
  { x: 38, y: 62, delay: 1.1, size: 4 },
  { x: 72, y: 22, delay: 0.4, size: 4 },
  { x: 22, y: 50, delay: 3.3, size: 4 },
  { x: 88, y: 85, delay: 2.0, size: 4 },
  { x: 50, y: 35, delay: 1.7, size: 4 },
  { x: 15, y: 68, delay: 0.8, size: 4 },
  { x: 60, y: 48, delay: 2.5, size: 4 },
  { x: 82, y: 15, delay: 3.9, size: 4 },
  { x: 35, y: 25, delay: 1.3, size: 4 },
  { x: 68, y: 65, delay: 0.2, size: 4 },
  { x: 3, y: 82, delay: 2.8, size: 4 },
  { x: 48, y: 78, delay: 1.6, size: 4 },
  { x: 75, y: 42, delay: 3.5, size: 4 },
];

export default function CTASection() {
  const containerRef = useScrollReveal({ y: 50, stagger: 0.12 });

  return (
    <section id="cta" className="landing-section bg-bg relative overflow-hidden">
      {/* ── Perspective grid ── */}
      <div className="perspective-grid" aria-hidden="true" />

      {/* ── Particle dots ── */}
      {PARTICLE_DOTS.map((dot, i) => (
        <div
          key={i}
          className="absolute w-1 h-1 rounded-full bg-white/[0.05] float-gentle"
          style={{
            left: `${dot.x}%`,
            top: `${dot.y}%`,
            animationDelay: `${dot.delay}s`,
            animationDuration: `${6 + (i % 4)}s`,
          }}
          aria-hidden="true"
        />
      ))}

      {/* ── Content ── */}
      <div ref={containerRef} className="landing-container relative z-10 text-center py-32">
        <span className="reveal-item font-mono text-[11px] tracking-[0.10em] uppercase text-[#00C896] mb-6 block">
          GET STARTED
        </span>

        <h2 className="reveal-item font-space text-[clamp(2rem,5vw,3.5rem)] font-bold text-text-1 mb-6">
          Ready to Transform Road Safety?
        </h2>

        <p className="reveal-item text-lg text-text-2 mb-12 max-w-xl mx-auto">
          Join the intelligence network protecting India&apos;s roads.
        </p>

        {/* ── CTA Buttons ── */}
        <div className="reveal-item flex flex-wrap justify-center gap-4">
          {/* Primary — Launch Platform */}
          <Link
            href="/login"
            className="bg-brand hover:bg-brand-hover text-white px-8 py-4 rounded-lg text-sm font-semibold uppercase tracking-wider transition-all hover:-translate-y-0.5 hover:shadow-brand inline-flex items-center justify-center"
          >
            Launch Platform
          </Link>

          {/* Secondary — Explore Intelligence */}
          <Link
            href="/"
            className="bg-white/[0.04] hover:bg-white/[0.08] border border-white/[0.08] text-text-1 px-8 py-4 rounded-lg text-sm font-semibold transition-all inline-flex items-center justify-center"
          >
            Explore Intelligence
          </Link>

          {/* Tertiary — GitHub */}
          <a
            href="https://github.com/SafeVixAI/SafeVixAI"
            target="_blank"
            rel="noopener noreferrer"
            className="text-[#00C896] hover:text-white text-sm font-semibold transition-colors flex items-center gap-2 px-4 py-4"
          >
            View GitHub
            <ExternalLink size={14} aria-hidden="true" />
          </a>
        </div>
      </div>
    </section>
  );
}