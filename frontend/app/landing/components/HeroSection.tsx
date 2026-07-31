'use client';

// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
import React from 'react';


import { useRef, useCallback } from 'react';
import Link from 'next/link';
import dynamic from 'next/dynamic';
import { useGSAP } from '@gsap/react';
import { gsap } from '@/lib/gsap';

/* ────────────────────────────────────────────────────────────
   SafeVixAI Landing — Cinematic Hero Section
   ──────────────────────────────────────────────────────────── */

const splitText = (text: string) => {
  return text.split('').map((char, index) => (
    <span key={index} className="inline-block" style={{ opacity: 0, display: 'inline-block' }}>
      {char === ' ' ? '\u00A0' : char}
    </span>
  ));
};

/* ── Dynamic 3D Globe (SSR disabled) ── */
const GlobeScene = dynamic(
  () => import('./three/IntelligenceGlobe'),
  {
    ssr: false,
    loading: () => <GlobeFallback />,
  }
);

/* ── Globe Fallback — pulsing ring ── */
function GlobeFallback() {
  return (
    <div className="w-full h-full flex items-center justify-center">
      <div className="relative w-48 h-48">
        {/* Outer pulsing ring */}
        <div
          className="absolute inset-0 rounded-full border border-brand-light/20"
          style={{
            animation: 'globe-fallback-pulse 2.5s ease-in-out infinite',
          }}
        />
        {/* Inner pulsing ring */}
        <div
          className="absolute inset-6 rounded-full border border-brand-light/30"
          style={{
            animation: 'globe-fallback-pulse 2.5s ease-in-out infinite 0.4s',
          }}
        />
        {/* Core dot */}
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="w-3 h-3 rounded-full bg-brand-light/60 animate-pulse" />
        </div>
      </div>
      <style jsx>{`
        @keyframes globe-fallback-pulse {
          0%, 100% { transform: scale(1); opacity: 0.4; }
          50% { transform: scale(1.08); opacity: 0.8; }
        }
      `}</style>
    </div>
  );
}

/* ── Floating Stat Panel ── */
interface StatPanelProps {
  label: string;
  value: string;
  accentColor: 'red' | 'green' | 'amber';
  className?: string;
  animClass?: string;
}

function StatPanel({ label, value, accentColor, className = '', animClass = 'float-gentle' }: StatPanelProps) {
  const dotColors = {
    red: 'bg-emergency',
    green: 'bg-brand-light',
    amber: 'bg-warning',
  } as const;

  const valueColors = {
    red: 'text-emergency',
    green: 'text-brand-light',
    amber: 'text-warning',
  } as const;

  return (
    <div
      className={`
        stat-panel
        bg-surface-1/80 backdrop-blur-xl
        border border-white/[0.06] rounded-lg
        px-4 py-3 shadow-panel
        ${animClass} ${className}
      `}
    >
      <div className="flex items-center gap-2 mb-1">
        <div className={`w-1.5 h-1.5 rounded-full ${dotColors[accentColor]}`} />
        <span className="font-mono text-[10px] font-semibold tracking-wider uppercase text-text-3">
          {label}
        </span>
      </div>
      <span className={`font-space text-xl font-bold ${valueColors[accentColor]}`}>
        {value}
      </span>
    </div>
  );
}

/* ── Main Hero Section ── */
export default function HeroSection() {
  const sectionRef = useRef<HTMLElement>(null);
  const overlineRef = useRef<HTMLParagraphElement>(null);
  const headlineRef = useRef<HTMLHeadingElement>(null);
  const descRef = useRef<HTMLParagraphElement>(null);
  const buttonsRef = useRef<HTMLDivElement>(null);
  const statusRef = useRef<HTMLDivElement>(null);
  const statusTextRef = useRef<HTMLSpanElement>(null);
  const panelsRef = useRef<HTMLDivElement>(null);

  /* ── GSAP staggered entry animations ── */
  useGSAP(
    () => {
      if (!sectionRef.current) return;

      const prefersReducedMotion = window.matchMedia(
        '(prefers-reduced-motion: reduce)'
      ).matches;

      if (prefersReducedMotion) {
        // Show everything immediately
        gsap.set(
          [
            overlineRef.current,
            headlineRef.current,
            descRef.current,
            buttonsRef.current?.children,
            statusRef.current,
            panelsRef.current?.querySelectorAll('.stat-panel'),
          ].filter(Boolean),
          { opacity: 1, y: 0, x: 0 }
        );
        return;
      }

      const tl = gsap.timeline({ defaults: { ease: 'power3.out' } });

      // Overline
      if (overlineRef.current) {
        const text = "National Road Safety Intelligence";
        overlineRef.current.textContent = "";
        overlineRef.current.classList.add('typewriter-cursor');
        gsap.set(overlineRef.current, { opacity: 1 });
        const obj = { len: 0 };
        tl.to(obj, {
          len: text.length,
          duration: 1.5,
          ease: "none",
          onUpdate: () => {
            if (overlineRef.current) {
              overlineRef.current.textContent = text.substring(0, Math.floor(obj.len));
            }
          },
          onComplete: () => {
            overlineRef.current?.classList.remove('typewriter-cursor');
          }
        }, 0.2);
      }

      // Headline
      if (headlineRef.current) {
        const chars = headlineRef.current.querySelectorAll('span > span');
        gsap.set(headlineRef.current, { opacity: 1 });
        tl.fromTo(
          chars,
          { opacity: 0, y: 40, rotateX: -90 },
          { opacity: 1, y: 0, rotateX: 0, stagger: 0.02, duration: 0.8 },
          0.4
        );
      }

      // Description
      if (descRef.current) {
        tl.fromTo(
          descRef.current,
          { opacity: 0, y: 20 },
          { opacity: 1, y: 0, duration: 0.6 },
          0.7
        );
      }

      // Buttons (stagger children)
      if (buttonsRef.current) {
        tl.fromTo(
          buttonsRef.current.children,
          { opacity: 0, y: 20 },
          { opacity: 1, y: 0, stagger: 0.1, duration: 0.5 },
          0.9
        );
      }

      // Status line
      if (statusRef.current && statusTextRef.current) {
        tl.fromTo(
          statusRef.current,
          { opacity: 0 },
          { opacity: 1, duration: 0.2 },
          1.2
        );
        const text = "System Online — Monitoring Active";
        statusTextRef.current.textContent = "";
        const obj = { len: 0 };
        tl.to(obj, {
          len: text.length,
          duration: 1.5,
          ease: "none",
          onUpdate: () => {
            if (statusTextRef.current) {
              statusTextRef.current.textContent = text.substring(0, Math.floor(obj.len));
            }
          }
        }, 1.4);
      }

      // Floating panels (slide in from right)
      if (panelsRef.current) {
        const panels = panelsRef.current.querySelectorAll('.stat-panel');
        if (panels.length > 0) {
          tl.fromTo(
            panels,
            { opacity: 0, x: 30 },
            { opacity: 1, x: 0, stagger: 0.15, duration: 0.6 },
            1.0
          );

          // Continuous yoyo float after entry
          gsap.to(panels, {
            y: -8,
            duration: 3,
            stagger: 0.5,
            ease: 'sine.inOut',
            yoyo: true,
            repeat: -1,
            delay: 2,
          });
        }
      }
    },
    { scope: sectionRef }
  );

  const handleMouseMove = useCallback((e: React.MouseEvent<HTMLElement>) => {
    if (!sectionRef.current) return;
    const rect = sectionRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    sectionRef.current.style.setProperty('--mouse-x', `${x}px`);
    sectionRef.current.style.setProperty('--mouse-y', `${y}px`);
  }, []);

  return (
    <section
      ref={sectionRef}
      id="platform"
      onMouseMove={handleMouseMove}
      className="relative min-h-dvh hero-gradient-bg grid-pattern overflow-hidden"
    >
      {/* Mouse follower glow */}
      <div className="hidden lg:block absolute inset-0 pointer-events-none z-0" style={{ background: 'radial-gradient(600px circle at var(--mouse-x, 50%) var(--mouse-y, 50%), rgba(0,200,150,0.04), transparent 40%)' }} />
      {/* ── Content Grid ── */}
      <div className="landing-container grid grid-cols-1 lg:grid-cols-2 gap-8 lg:gap-12 min-h-dvh">
        {/* ── Left Column: Text Content ── */}
        <div className="flex flex-col justify-center py-24 lg:py-16 relative z-10">
          {/* Overline */}
          <p
            ref={overlineRef}
            className="font-mono text-[11px] font-semibold tracking-[0.10em] uppercase text-brand-light mb-6"
            style={{ opacity: 1 }}
          >
            National Road Safety Intelligence
          </p>

          {/* Headline */}
          <h1
            ref={headlineRef}
            className="font-space text-[clamp(2.5rem,6vw,4.5rem)] font-bold leading-[1.05] tracking-tight text-text-1 mb-6 text-gradient-animated"
            style={{ opacity: 1 }}
            aria-label="India's AI-Powered Road Safety Infrastructure"
          >
            <span className="inline-block">{splitText("India's AI-Powered")}</span>
            <br />
            <span className="inline-block">{splitText("Road Safety")}</span>
            <br />
            <span className="inline-block">{splitText("Infrastructure")}</span>
          </h1>

          {/* Description */}
          <p
            ref={descRef}
            className="text-lg text-text-2 max-w-lg mb-10 leading-relaxed"
            style={{ opacity: 0 }}
          >
            Real-time accident detection, emergency response routing, and
            hazard intelligence — protecting 1.4 billion lives.
          </p>

          {/* Button Group */}
          <div
            ref={buttonsRef}
            className="flex flex-wrap gap-4"
            style={{ opacity: 0 }}
          >
            <Link
              href="/login"
              className="
                inline-flex items-center justify-center
                bg-brand hover:bg-brand-hover text-white
                px-7 py-3.5 rounded-lg text-sm font-semibold
                uppercase tracking-wider
                transition-all duration-200
                hover:-translate-y-0.5 hover:shadow-brand
                shimmer-on-hover magnetic-cta
              "
            >
              Launch Platform
            </Link>
            <Link
              href="/signup"
              className="
                inline-flex items-center justify-center
                bg-white/[0.04] hover:bg-white/[0.08]
                text-text-1
                border border-white/[0.08] hover:border-brand/30
                px-7 py-3.5 rounded-lg text-sm font-semibold
                transition-all duration-200
                uppercase tracking-wider
                shimmer-on-hover
              "
            >
              Create Account
            </Link>
            <a
              href="#modules"
              onClick={(e) => {
                e.preventDefault();
                document
                  .querySelector('#modules')
                  ?.scrollIntoView({ behavior: 'smooth', block: 'start' });
              }}
              className="
                inline-flex items-center justify-center
                text-text-2 hover:text-text-1
                px-4 py-3.5 text-sm font-semibold
                transition-all duration-200
                underline underline-offset-4 decoration-white/20 hover:decoration-white/40
              "
            >
              Explore Intelligence
            </a>
          </div>

          {/* Status Line */}
          <div
            ref={statusRef}
            className="flex items-center gap-2 mt-8"
            style={{ opacity: 0 }}
          >
            <div className="w-2 h-2 rounded-full bg-brand-light animate-pulse" />
            <span ref={statusTextRef} className="text-xs text-text-3 font-mono uppercase tracking-wider">
              System Online — Monitoring Active
            </span>
          </div>
        </div>

        {/* ── Right Column: 3D Globe + Stat Panels ── */}
        <div className="hidden lg:flex items-center justify-center relative">
          <div className="relative w-full h-[600px] lg:h-full">
            {/* 3D Canvas */}
            <GlobeScene />

            {/* Floating stat panels */}
            <div ref={panelsRef} className="absolute inset-0 pointer-events-none">
              <StatPanel
                label="Active Incidents"
                value="47"
                accentColor="red"
                className="absolute top-[12%] right-[4%]"
                animClass=""
              />
              <StatPanel
                label="SOS Active"
                value="3"
                accentColor="red"
                className="absolute top-[44%] right-[0%]"
                animClass=""
              />
              <StatPanel
                label="Hazards Monitored"
                value="1,247"
                accentColor="amber"
                className="absolute bottom-[18%] right-[6%]"
                animClass=""
              />
            </div>
          </div>
        </div>
      </div>

      {/* ── Bottom fade gradient ── */}
      <div
        className="absolute bottom-0 left-0 right-0 h-32 pointer-events-none z-10"
        style={{
          background:
            'linear-gradient(to top, var(--bg), transparent)',
        }}
      />
    </section>
  );
}