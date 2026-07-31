'use client';

// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
import React from 'react';


import { useRef, useEffect, useCallback } from 'react';
import { useGSAP } from '@gsap/react';
import { gsap } from '@/lib/gsap';
import { useScrollReveal, useTextReveal } from '../hooks/useLandingGSAP';

/* ── Shield SVG (decorative) ── */
function ShieldMark() {
  return (
    <svg
      width={48}
      height={48}
      viewBox="0 0 64 64"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className="opacity-30 mx-auto sv-glow-breathe"
      aria-hidden="true"
    >
      <path
        d="M32 4L8 16v16c0 14.4 10.24 27.84 24 32 13.76-4.16 24-17.6 24-32V16L32 4z"
        fill="rgba(26,92,56,0.15)"
        stroke="#00C896"
        strokeWidth="1.5"
        strokeOpacity="0.3"
      />
      <path
        d="M32 14l-16 8v12c0 10.4 6.88 19.84 16 22.4 9.12-2.56 16-12 16-22.4V22l-16-8z"
        fill="rgba(0,200,150,0.06)"
        stroke="#00C896"
        strokeWidth="0.75"
        strokeOpacity="0.2"
      />
      <text
        x="32"
        y="38"
        textAnchor="middle"
        fill="#00C896"
        fontFamily="Space Grotesk, sans-serif"
        fontSize="11"
        fontWeight="700"
        opacity="0.5"
      >
        SVA
      </text>
    </svg>
  );
}

export default function MissionSection() {
  const headingRef = useTextReveal();
  const containerRef = useScrollReveal({ y: 30, stagger: 0.15 });
  const sectionRef = useRef<HTMLElement>(null);
  const beam1Ref = useRef<HTMLDivElement>(null);
  const beam2Ref = useRef<HTMLDivElement>(null);

  /* ── Parallax beams on scroll ── */
  useGSAP(
    () => {
      if (!sectionRef.current) return;
      const prefersReducedMotion = window.matchMedia(
        '(prefers-reduced-motion: reduce)'
      ).matches;
      if (prefersReducedMotion) return;

      // Beam 1 — slow drift
      if (beam1Ref.current) {
        gsap.to(beam1Ref.current, {
          rotation: '+=6',
          y: -30,
          scrollTrigger: {
            trigger: sectionRef.current,
            start: 'top bottom',
            end: 'bottom top',
            scrub: 1.5,
          },
        });
      }

      // Beam 2 — counter drift
      if (beam2Ref.current) {
        gsap.to(beam2Ref.current, {
          rotation: '-=5',
          y: 20,
          scrollTrigger: {
            trigger: sectionRef.current,
            start: 'top bottom',
            end: 'bottom top',
            scrub: 2,
          },
        });
      }
    },
    { scope: sectionRef }
  );

  /* ── Subtle mouse parallax on glow ── */
  const handleMouseMove = useCallback((e: React.MouseEvent<HTMLElement>) => {
    if (!sectionRef.current) return;
    const rect = sectionRef.current.getBoundingClientRect();
    const x = ((e.clientX - rect.left) / rect.width) * 100;
    const y = ((e.clientY - rect.top) / rect.height) * 100;
    sectionRef.current.style.setProperty('--glow-x', `${x}%`);
    sectionRef.current.style.setProperty('--glow-y', `${y}%`);
  }, []);

  return (
    <section
      id="mission"
      ref={sectionRef}
      onMouseMove={handleMouseMove}
      className="landing-section bg-bg min-h-[80vh] flex items-center justify-center relative overflow-hidden"
    >
      {/* ── Interactive radial glow ── */}
      <div
        className="absolute inset-0 pointer-events-none hidden lg:block"
        style={{
          background:
            'radial-gradient(ellipse 500px 400px at var(--glow-x, 50%) var(--glow-y, 50%), rgba(0,200,150,0.05), transparent)',
          transition: 'background 0.3s ease',
        }}
        aria-hidden="true"
      />
      {/* Fallback glow for mobile */}
      <div
        className="absolute inset-0 pointer-events-none lg:hidden"
        style={{
          background:
            'radial-gradient(ellipse 600px 400px at 50% 50%, rgba(0,200,150,0.04), transparent)',
        }}
        aria-hidden="true"
      />

      {/* ── Animated diagonal light beams ── */}
      <div
        ref={beam1Ref}
        className="absolute top-0 left-1/4 w-px h-full pointer-events-none beam-animated"
        style={{
          background:
            'linear-gradient(to bottom, transparent 0%, rgba(255,255,255,0.03) 30%, rgba(255,255,255,0.04) 50%, rgba(255,255,255,0.03) 70%, transparent 100%)',
          transform: 'rotate(15deg)',
          transformOrigin: 'top center',
          ['--beam-start' as string]: '15deg',
          ['--beam-end' as string]: '18deg',
        }}
        aria-hidden="true"
      />
      <div
        ref={beam2Ref}
        className="absolute top-0 right-1/3 w-px h-full pointer-events-none beam-animated"
        style={{
          background:
            'linear-gradient(to bottom, transparent 0%, rgba(255,255,255,0.02) 20%, rgba(255,255,255,0.03) 50%, rgba(255,255,255,0.02) 80%, transparent 100%)',
          transform: 'rotate(-12deg)',
          transformOrigin: 'top center',
          animationDelay: '-3s',
          ['--beam-start' as string]: '-12deg',
          ['--beam-end' as string]: '-9deg',
        }}
        aria-hidden="true"
      />
      {/* ── Extra subtle beam ── */}
      <div
        className="absolute top-0 left-2/3 w-px h-full pointer-events-none beam-animated"
        style={{
          background:
            'linear-gradient(to bottom, transparent 0%, rgba(0,200,150,0.015) 40%, rgba(0,200,150,0.02) 60%, transparent 100%)',
          transform: 'rotate(8deg)',
          transformOrigin: 'top center',
          animationDelay: '-5s',
          ['--beam-start' as string]: '8deg',
          ['--beam-end' as string]: '11deg',
        }}
        aria-hidden="true"
      />

      {/* ── Content ── */}
      <div ref={containerRef} className="relative z-10 text-center max-w-4xl mx-auto px-6">
        <h2
          ref={headingRef as React.RefObject<HTMLHeadingElement>}
          className="font-space text-[clamp(1.75rem,4.5vw,3.5rem)] font-bold text-text-1 leading-tight"
        >
          Building India&apos;s Next Generation Road Safety Intelligence Infrastructure.
        </h2>

        <p className="reveal-item text-xl text-text-2 mt-8">
          Every second counts. Every life matters.
        </p>

        <div className="reveal-item mt-12">
          <ShieldMark />
        </div>
      </div>
    </section>
  );
}