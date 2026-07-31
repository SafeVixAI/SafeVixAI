'use client';

// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
import React from 'react';


import { useRef, useCallback } from 'react';
import Link from 'next/link';
import { ExternalLink } from 'lucide-react';
import { useGSAP } from '@gsap/react';
import { gsap } from '@/lib/gsap';
import { useScrollReveal } from '../hooks/useLandingGSAP';

/* ── Particle dot positions — pre-generated for determinism ── */
const PARTICLE_DOTS: { x: number; y: number; delay: number; size: number; depth: number }[] = [
  { x: 5, y: 12, delay: 0, size: 4, depth: 1 },
  { x: 92, y: 8, delay: 1.2, size: 4, depth: 2 },
  { x: 18, y: 78, delay: 2.4, size: 4, depth: 1 },
  { x: 85, y: 72, delay: 0.6, size: 4, depth: 3 },
  { x: 42, y: 5, delay: 1.8, size: 4, depth: 2 },
  { x: 65, y: 88, delay: 3.0, size: 4, depth: 1 },
  { x: 10, y: 45, delay: 0.3, size: 4, depth: 2 },
  { x: 78, y: 38, delay: 2.1, size: 4, depth: 3 },
  { x: 30, y: 92, delay: 1.5, size: 4, depth: 1 },
  { x: 55, y: 15, delay: 0.9, size: 4, depth: 2 },
  { x: 8, y: 28, delay: 3.6, size: 4, depth: 1 },
  { x: 95, y: 55, delay: 2.7, size: 4, depth: 3 },
  { x: 38, y: 62, delay: 1.1, size: 4, depth: 2 },
  { x: 72, y: 22, delay: 0.4, size: 4, depth: 1 },
  { x: 22, y: 50, delay: 3.3, size: 4, depth: 3 },
  { x: 88, y: 85, delay: 2.0, size: 4, depth: 2 },
  { x: 50, y: 35, delay: 1.7, size: 4, depth: 1 },
  { x: 15, y: 68, delay: 0.8, size: 4, depth: 2 },
  { x: 60, y: 48, delay: 2.5, size: 4, depth: 3 },
  { x: 82, y: 15, delay: 3.9, size: 4, depth: 1 },
  { x: 35, y: 25, delay: 1.3, size: 4, depth: 2 },
  { x: 68, y: 65, delay: 0.2, size: 4, depth: 3 },
  { x: 3, y: 82, delay: 2.8, size: 4, depth: 1 },
  { x: 48, y: 78, delay: 1.6, size: 4, depth: 2 },
  { x: 75, y: 42, delay: 3.5, size: 4, depth: 3 },
];

export default function CTASection() {
  const containerRef = useScrollReveal({ y: 50, stagger: 0.12 });
  const sectionRef = useRef<HTMLElement>(null);
  const gridRef = useRef<HTMLDivElement>(null);
  const primaryBtnRef = useRef<HTMLAnchorElement>(null);

  /* ── Mouse parallax on grid + particles ── */
  const handleMouseMove = useCallback(
    (e: React.MouseEvent<HTMLElement>) => {
      if (!sectionRef.current) return;
      const prefersReducedMotion = window.matchMedia(
        '(prefers-reduced-motion: reduce)'
      ).matches;
      if (prefersReducedMotion) return;

      const rect = sectionRef.current.getBoundingClientRect();
      const mouseX = (e.clientX - rect.left) / rect.width - 0.5;
      const mouseY = (e.clientY - rect.top) / rect.height - 0.5;

      // Subtle grid perspective shift
      if (gridRef.current) {
        gsap.to(gridRef.current, {
          rotateY: mouseX * 3,
          rotateX: -mouseY * 2 + 60,
          duration: 0.8,
          ease: 'power2.out',
          overwrite: 'auto',
        });
      }

      // Magnetic primary button
      if (primaryBtnRef.current) {
        const btnRect = primaryBtnRef.current.getBoundingClientRect();
        const btnCenterX = btnRect.left + btnRect.width / 2;
        const btnCenterY = btnRect.top + btnRect.height / 2;
        const distX = e.clientX - btnCenterX;
        const distY = e.clientY - btnCenterY;
        const distance = Math.sqrt(distX * distX + distY * distY);

        if (distance < 200) {
          const pull = (1 - distance / 200) * 0.3;
          gsap.to(primaryBtnRef.current, {
            x: distX * pull,
            y: distY * pull,
            duration: 0.4,
            ease: 'power2.out',
            overwrite: 'auto',
          });
        } else {
          gsap.to(primaryBtnRef.current, {
            x: 0,
            y: 0,
            duration: 0.6,
            ease: 'power3.out',
            overwrite: 'auto',
          });
        }
      }
    },
    []
  );

  const handleMouseLeave = useCallback(() => {
    if (primaryBtnRef.current) {
      gsap.to(primaryBtnRef.current, {
        x: 0,
        y: 0,
        duration: 0.6,
        ease: 'power3.out',
        overwrite: 'auto',
      });
    }
    if (gridRef.current) {
      gsap.to(gridRef.current, {
        rotateY: 0,
        rotateX: 60,
        duration: 0.8,
        ease: 'power2.out',
        overwrite: 'auto',
      });
    }
  }, []);

  /* ── CTA headline entrance ── */
  const headlineRef = useRef<HTMLHeadingElement>(null);

  useGSAP(
    () => {
      if (!headlineRef.current || !sectionRef.current) return;
      const prefersReducedMotion = window.matchMedia(
        '(prefers-reduced-motion: reduce)'
      ).matches;
      if (prefersReducedMotion) return;

      gsap.fromTo(
        headlineRef.current,
        { scale: 0.92, opacity: 0, filter: 'blur(8px)' },
        {
          scale: 1,
          opacity: 1,
          filter: 'blur(0px)',
          duration: 1,
          ease: 'power3.out',
          scrollTrigger: {
            trigger: headlineRef.current,
            start: 'top 85%',
            toggleActions: 'play none none none',
          },
        }
      );
    },
    { scope: sectionRef }
  );

  return (
    <section
      id="cta"
      ref={sectionRef}
      className="landing-section bg-bg relative overflow-hidden"
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
    >
      {/* ── Perspective grid with mouse tracking ── */}
      <div
        ref={gridRef}
        className="absolute inset-0 pointer-events-none"
        style={{
          backgroundImage:
            'linear-gradient(rgba(0,200,150,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(0,200,150,0.03) 1px, transparent 1px)',
          backgroundSize: '80px 80px',
          transform: 'perspective(500px) rotateX(60deg)',
          transformOrigin: 'center top',
          maskImage: 'linear-gradient(to bottom, transparent, white 20%, white 60%, transparent)',
          WebkitMaskImage: 'linear-gradient(to bottom, transparent, white 20%, white 60%, transparent)',
        }}
        aria-hidden="true"
      />

      {/* ── Particle dots with depth layers ── */}
      {PARTICLE_DOTS.map((dot, i) => (
        <div
          key={i}
          className="absolute rounded-full float-gentle"
          style={{
            left: `${dot.x}%`,
            top: `${dot.y}%`,
            width: `${dot.depth === 3 ? 2 : dot.depth === 2 ? 1.5 : 1}px`,
            height: `${dot.depth === 3 ? 2 : dot.depth === 2 ? 1.5 : 1}px`,
            backgroundColor: `rgba(255,255,255,${dot.depth === 3 ? 0.08 : dot.depth === 2 ? 0.05 : 0.03})`,
            animationDelay: `${dot.delay}s`,
            animationDuration: `${6 + (i % 4)}s`,
          }}
          aria-hidden="true"
        />
      ))}

      {/* ── Ambient glow ── */}
      <div
        className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] pointer-events-none"
        style={{
          background: 'radial-gradient(circle, rgba(0,200,150,0.05), transparent 60%)',
        }}
        aria-hidden="true"
      />

      {/* ── Content ── */}
      <div ref={containerRef} className="landing-container relative z-10 text-center py-32">
        <span className="reveal-item font-mono text-[11px] tracking-[0.10em] uppercase text-[#00C896] mb-6 block">
          GET STARTED
        </span>

        <h2
          ref={headlineRef}
          className="reveal-item font-space text-[clamp(2rem,5vw,3.5rem)] font-bold text-text-1 mb-6"
        >
          Ready to Transform Road Safety?
        </h2>

        <p className="reveal-item text-lg text-text-2 mb-12 max-w-xl mx-auto">
          Join the intelligence network protecting India&apos;s roads.
        </p>

        {/* ── CTA Buttons ── */}
        <div className="reveal-item flex flex-wrap justify-center gap-4">
          {/* Primary — Launch Platform (magnetic + shimmer) */}
          <Link
            ref={primaryBtnRef}
            href="/login"
            className="magnetic-cta shimmer-on-hover bg-brand hover:bg-brand-hover text-white px-8 py-4 rounded-lg text-sm font-semibold uppercase tracking-wider transition-all hover:-translate-y-0.5 hover:shadow-brand inline-flex items-center justify-center"
          >
            Launch Platform
          </Link>

          {/* Secondary — Explore Intelligence */}
          <Link
            href="/"
            className="shimmer-on-hover bg-white/[0.04] hover:bg-white/[0.08] border border-white/[0.08] hover:border-brand/30 text-text-1 px-8 py-4 rounded-lg text-sm font-semibold transition-all inline-flex items-center justify-center"
          >
            Explore Intelligence
          </Link>

          {/* Tertiary — GitHub */}
          <a
            href="https://github.com/SafeVixAI/SafeVixAI"
            target="_blank"
            rel="noopener noreferrer"
            className="text-[#00C896] hover:text-white text-sm font-semibold transition-colors flex items-center gap-2 px-4 py-4 group"
          >
            View GitHub
            <ExternalLink size={14} aria-hidden="true" className="transition-transform duration-300 group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
          </a>
        </div>
      </div>
    </section>
  );
}