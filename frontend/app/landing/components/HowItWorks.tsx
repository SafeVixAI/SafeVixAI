// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
import React from 'react';

'use client';

import { useRef, useState, useEffect } from 'react';
import { useGSAP } from '@gsap/react';
import { gsap } from '@/lib/gsap';
import { useScrollReveal } from '../hooks/useLandingGSAP';
import {
  Zap,
  Brain,
  Timer,
  Shield,
  Route,
  Users,
  type LucideIcon,
} from 'lucide-react';

/* ═══════════════════════════════════════════════════════
   STAGE DATA
   ═══════════════════════════════════════════════════════ */

interface Stage {
  icon: LucideIcon;
  title: string;
  desc: string;
  color: string;
}

const STAGES: Stage[] = [
  {
    icon: Zap,
    title: 'Crash Detected',
    desc: 'AI-powered accelerometer detects impact force exceeding safety thresholds in real-time.',
    color: '#DC2626',
  },
  {
    icon: Brain,
    title: 'AI Analysis',
    desc: 'Machine learning classifies severity and determines emergency response level within 2 seconds.',
    color: '#3B82F6',
  },
  {
    icon: Timer,
    title: 'Emergency Countdown',
    desc: '15-second SOS countdown with automatic cancellation if the driver responds.',
    color: '#D97706',
  },
  {
    icon: Shield,
    title: 'SOS Triggered',
    desc: 'Emergency services notified with precise GPS coordinates and crash severity data.',
    color: '#DC2626',
  },
  {
    icon: Route,
    title: 'Hospital Routing',
    desc: 'Nearest hospital route calculated. Ambulance dispatched with real-time traffic optimization.',
    color: '#00C896',
  },
  {
    icon: Users,
    title: 'Family Tracking',
    desc: 'Live location shared with emergency contacts. Real-time tracking until safety confirmed.',
    color: '#00C896',
  },
];

const STAGE_COUNT = STAGES.length;

/* ═══════════════════════════════════════════════════════
   Desktop Stage Panel
   ═══════════════════════════════════════════════════════ */

function DesktopStagePanel({ stage, index }: { stage: Stage; index: number }) {
  const Icon = stage.icon;

  return (
    <div className="how-it-works-stage">
      <div className="landing-container w-full">
        <div className="grid grid-cols-2 items-center gap-12 lg:gap-20">
          {/* Left — Text content */}
          <div className="flex flex-col">
            <span
              className="font-mono text-[clamp(80px,10vw,120px)] font-extrabold leading-none select-none"
              style={{ color: 'rgba(255,255,255,0.03)' }}
            >
              {String(index + 1).padStart(2, '0')}
            </span>
            <h3 className="font-space text-4xl font-bold text-text-1 mb-4 -mt-4">
              {stage.title}
            </h3>
            <p className="text-lg text-text-2 max-w-md leading-relaxed">
              {stage.desc}
            </p>
            {/* Stage progress dots */}
            <div className="flex items-center gap-2 mt-8">
              {STAGES.map((s, i) => (
                <div
                  key={s.title}
                  className="w-2 h-2 rounded-full transition-all duration-300"
                  style={{
                    backgroundColor: i === index ? stage.color : 'rgba(255,255,255,0.1)',
                    transform: i === index ? 'scale(1.5)' : 'scale(1)',
                  }}
                />
              ))}
            </div>
          </div>

          {/* Right — Icon display */}
          <div className="flex items-center justify-center">
            <div className="relative">
              {/* Outer glow ring */}
              <div
                className="absolute inset-0 rounded-full blur-2xl opacity-20"
                style={{ backgroundColor: stage.color }}
              />
              {/* Ring border */}
              <div
                className="relative w-48 h-48 rounded-full border-2 flex items-center justify-center"
                style={{ borderColor: `${stage.color}30` }}
              >
                {/* Inner icon circle */}
                <div
                  className="w-28 h-28 rounded-full flex items-center justify-center"
                  style={{ backgroundColor: `${stage.color}15` }}
                >
                  <Icon
                    size={56}
                    strokeWidth={1.5}
                    style={{ color: stage.color }}
                  />
                </div>
                {/* Orbiting dot */}
                <div
                  className="absolute w-3 h-3 rounded-full orbit-ring"
                  style={{
                    backgroundColor: stage.color,
                    top: '-6px',
                    left: '50%',
                    marginLeft: '-6px',
                    boxShadow: `0 0 12px ${stage.color}80`,
                  }}
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════
   Mobile Stage Card
   ═══════════════════════════════════════════════════════ */

function MobileStageCard({ stage, index }: { stage: Stage; index: number }) {
  const Icon = stage.icon;

  return (
    <div className="reveal-item bg-surface-1 border border-white/[0.06] rounded-xl p-6 relative overflow-hidden">
      {/* Top color accent */}
      <div
        className="absolute top-0 left-0 right-0 h-[2px]"
        style={{ backgroundColor: stage.color }}
      />

      <div className="flex items-start gap-5">
        {/* Icon */}
        <div
          className="w-14 h-14 rounded-xl flex-shrink-0 flex items-center justify-center"
          style={{ backgroundColor: `${stage.color}15` }}
        >
          <Icon size={28} strokeWidth={1.5} style={{ color: stage.color }} />
        </div>

        {/* Text */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-3 mb-2">
            <span
              className="font-mono text-xs font-semibold tracking-wider"
              style={{ color: stage.color }}
            >
              {String(index + 1).padStart(2, '0')}
            </span>
            <h3 className="font-space text-lg font-bold text-text-1">
              {stage.title}
            </h3>
          </div>
          <p className="text-sm text-text-2 leading-relaxed">{stage.desc}</p>
        </div>
      </div>

      {/* Connecting line to next stage */}
      {index < STAGE_COUNT - 1 && (
        <div className="absolute -bottom-[1px] left-10 w-[2px] h-6 -mb-6 z-10">
          <div
            className="w-full h-full"
            style={{
              background: `linear-gradient(to bottom, ${stage.color}40, transparent)`,
            }}
          />
        </div>
      )}
    </div>
  );
}

/* ═══════════════════════════════════════════════════════
   HowItWorks — Pinned horizontal scroll / mobile stack
   ═══════════════════════════════════════════════════════ */

export default function HowItWorks() {
  const sectionRef = useRef<HTMLDivElement>(null);
  const trackRef = useRef<HTMLDivElement>(null);
  const progressRef = useRef<HTMLDivElement>(null);
  const [isDesktop, setIsDesktop] = useState(false);
  const mobileContainerRef = useScrollReveal({ y: 40, stagger: 0.15 });

  // ── Media query detection ──
  useEffect(() => {
    /* istanbul ignore next */
if (typeof window === 'undefined') return;

    const mq = window.matchMedia('(min-width: 1024px)');
    const handler = (e: MediaQueryListEvent | MediaQueryList) => setIsDesktop(e.matches);
    handler(mq);
    mq.addEventListener('change', handler as (e: MediaQueryListEvent) => void);
    return () => mq.removeEventListener('change', handler as (e: MediaQueryListEvent) => void);
  }, []);

  // ── Desktop GSAP horizontal scroll ──
  useGSAP(
    () => {
      if (!isDesktop || !sectionRef.current || !trackRef.current) return;

      const prefersReducedMotion = window.matchMedia(
        '(prefers-reduced-motion: reduce)'
      ).matches;
      if (prefersReducedMotion) return;

      const totalPanels = STAGE_COUNT;
      const scrollDistance = trackRef.current.scrollWidth - window.innerWidth;

      gsap.to(trackRef.current, {
        x: -scrollDistance,
        ease: 'none',
        scrollTrigger: {
          trigger: sectionRef.current,
          pin: true,
          scrub: 1,
          snap: {
            snapTo: 1 / (totalPanels - 1),
            duration: { min: 0.2, max: 0.4 },
            ease: 'power1.inOut',
          },
          end: () => `+=${scrollDistance}`,
          invalidateOnRefresh: true,
          anticipatePin: 1,
          onUpdate: (self) => {
            if (progressRef.current) {
              progressRef.current.style.transform = `scaleX(${self.progress})`;
            }
          },
        },
      });
    },
    { scope: sectionRef, dependencies: [isDesktop] }
  );

  // ── Desktop Layout ──
  if (isDesktop) {
    return (
      <section
        id="how-it-works"
        ref={sectionRef}
        className="relative bg-bg overflow-hidden"
      >
        {/* Header — positioned inside the pinned viewport */}
        <div className="absolute top-0 left-0 right-0 z-10 pt-16 pointer-events-none">
          <div className="landing-container text-center">
            <p className="font-mono text-[11px] font-semibold tracking-[0.10em] uppercase text-brand-light mb-4">
              How It Works
            </p>
            <h2 className="font-space text-[clamp(1.75rem,4vw,3rem)] font-bold text-text-1">
              From Impact to Response in Seconds
            </h2>
          </div>
        </div>

        {/* Horizontal scroll track */}
        <div
          ref={trackRef}
          className="how-it-works-track"
        >
          {STAGES.map((stage, i) => (
            <DesktopStagePanel key={stage.title} stage={stage} index={i} />
          ))}
        </div>

        {/* Progress bar */}
        <div className="absolute bottom-0 left-0 right-0 h-[2px] bg-white/[0.06] z-20">
          <div
            ref={progressRef}
            className="h-full w-full origin-left bg-brand-light"
            style={{ transform: 'scaleX(0)' }}
          />
        </div>
      </section>
    );
  }

  // ── Mobile Layout ──
  return (
    <section id="how-it-works" className="landing-section bg-bg">
      <div ref={mobileContainerRef} className="landing-container">
        {/* Header */}
        <div className="text-center mb-12">
          <p className="reveal-item font-mono text-[11px] font-semibold tracking-[0.10em] uppercase text-brand-light mb-4">
            How It Works
          </p>
          <h2 className="reveal-item font-space text-[clamp(1.75rem,4vw,3rem)] font-bold text-text-1">
            From Impact to Response in Seconds
          </h2>
        </div>

        {/* Vertical card stack */}
        <div className="flex flex-col gap-4 max-w-xl mx-auto">
          {STAGES.map((stage, i) => (
            <MobileStageCard key={stage.title} stage={stage} index={i} />
          ))}
        </div>
      </div>
    </section>
  );
}
