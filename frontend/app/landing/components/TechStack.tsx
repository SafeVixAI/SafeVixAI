// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
import React from 'react';

'use client';

import { useRef, useEffect, useState } from 'react';
import { useScrollReveal } from '../hooks/useLandingGSAP';

/* ── Tech data ── */
interface TechItem {
  name: string;
  color: string;
}

const INNER_RING: TechItem[] = [
  { name: 'Next.js', color: '#FFFFFF' },
  { name: 'FastAPI', color: '#009688' },
  { name: 'Supabase', color: '#3ECF8E' },
];

const MIDDLE_RING: TechItem[] = [
  { name: 'Gemini AI', color: '#4285F4' },
  { name: 'Mapbox', color: '#4264FB' },
  { name: 'Three.js', color: '#049EF4' },
];

const OUTER_RING: TechItem[] = [
  { name: 'GSAP', color: '#88CE02' },
  { name: 'TensorFlow', color: '#FF6F00' },
  { name: 'Docker', color: '#2496ED' },
];

/* ── Orbital Item ── */
function OrbitalItem({
  item,
  index,
  total,
  radius,
  counterClass,
}: {
  item: TechItem;
  index: number;
  total: number;
  radius: number;
  counterClass: string;
}) {
  const angle = (360 / total) * index;

  return (
    <div
      className="absolute left-1/2 top-1/2"
      style={{
        transform: `rotate(${angle}deg) translateX(${radius}px) rotate(-${angle}deg)`,
        marginLeft: '-44px',
        marginTop: '-18px',
      }}
    >
      <div
        className={`${counterClass} flex items-center gap-2 bg-surface-1 border border-white/[0.06] rounded-lg px-3 py-2 shadow-card`}
      >
        <span
          className="w-2 h-2 rounded-full flex-shrink-0"
          style={{ backgroundColor: item.color }}
        />
        <span className="text-xs font-semibold text-text-1 whitespace-nowrap">
          {item.name}
        </span>
      </div>
    </div>
  );
}

/* ── Orbital Ring ── */
function OrbitalRing({
  items,
  radius,
  ringClass,
  counterClass,
}: {
  items: TechItem[];
  radius: number;
  ringClass: string;
  counterClass: string;
}) {
  const size = radius * 2;

  return (
    <div
      className={`${ringClass} absolute left-1/2 top-1/2 border border-white/[0.04] rounded-full`}
      style={{
        width: `${size}px`,
        height: `${size}px`,
        marginLeft: `-${radius}px`,
        marginTop: `-${radius}px`,
      }}
    >
      {items.map((item, i) => (
        <OrbitalItem
          key={item.name}
          item={item}
          index={i}
          total={items.length}
          radius={radius}
          counterClass={counterClass}
        />
      ))}
    </div>
  );
}

/* ── Shield SVG ── */
function ShieldLogo({ size = 64 }: { size?: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 64 64"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className="sv-glow-breathe"
    >
      <path
        d="M32 4L8 16v16c0 14.4 10.24 27.84 24 32 13.76-4.16 24-17.6 24-32V16L32 4z"
        fill="rgba(26,92,56,0.2)"
        stroke="#00C896"
        strokeWidth="1.5"
      />
      <path
        d="M32 14l-16 8v12c0 10.4 6.88 19.84 16 22.4 9.12-2.56 16-12 16-22.4V22l-16-8z"
        fill="rgba(0,200,150,0.08)"
        stroke="#00C896"
        strokeWidth="0.75"
        strokeOpacity="0.4"
      />
      <text
        x="32"
        y="38"
        textAnchor="middle"
        fill="#00C896"
        fontFamily="Space Grotesk, sans-serif"
        fontSize="11"
        fontWeight="700"
      >
        SVA
      </text>
    </svg>
  );
}

/* ── Mobile Grid Badge ── */
function TechBadge({ item }: { item: TechItem }) {
  return (
    <div className="reveal-item flex items-center gap-2 bg-surface-1 border border-white/[0.06] rounded-lg px-4 py-3 shadow-card">
      <span
        className="w-2 h-2 rounded-full flex-shrink-0"
        style={{ backgroundColor: item.color }}
      />
      <span className="text-xs font-semibold text-text-1">{item.name}</span>
    </div>
  );
}

/* ── Main Component ── */
export default function TechStack() {
  const containerRef = useScrollReveal({ y: 50, stagger: 0.08 });
  const orbitalRef = useRef<HTMLDivElement>(null);
  const [reducedMotion, setReducedMotion] = useState(false);

  useEffect(() => {
    const mq = window.matchMedia('(prefers-reduced-motion: reduce)');
    setReducedMotion(mq.matches);

    function handleChange(e: MediaQueryListEvent) {
      setReducedMotion(e.matches);
    }
    mq.addEventListener('change', handleChange);
    return () => mq.removeEventListener('change', handleChange);
  }, []);

  const allTech = [...INNER_RING, ...MIDDLE_RING, ...OUTER_RING];

  return (
    <section id="tech-stack" className="landing-section bg-bg">
      <div ref={containerRef} className="landing-container text-center">
        {/* ── Header ── */}
        <div className="reveal-item mb-16">
          <span className="font-mono text-[11px] tracking-[0.10em] uppercase text-brand-light block mb-3">
            TECHNOLOGY
          </span>
          <h2 className="font-space text-[clamp(1.75rem,4vw,3rem)] font-bold text-text-1">
            Built for Scale
          </h2>
        </div>

        {/* ── Orbital — desktop only ── */}
        <div className="reveal-item hidden md:flex justify-center">
          <div
            ref={orbitalRef}
            className="relative mx-auto"
            style={{ width: '560px', height: '560px' }}
            onMouseEnter={() => {
              if (!orbitalRef.current || reducedMotion) return;
              orbitalRef.current.querySelectorAll<HTMLElement>('.orbit-ring, .orbit-ring-reverse').forEach(el => {
                el.style.animationPlayState = 'paused';
              });
            }}
            onMouseLeave={() => {
              if (!orbitalRef.current || reducedMotion) return;
              orbitalRef.current.querySelectorAll<HTMLElement>('.orbit-ring, .orbit-ring-reverse').forEach(el => {
                el.style.animationPlayState = 'running';
              });
            }}
          >
            {/* Center Shield */}
            <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 z-10">
              <ShieldLogo size={64} />
            </div>

            {/* Inner Ring: r=120 */}
            <OrbitalRing
              items={INNER_RING}
              radius={120}
              ringClass={reducedMotion ? '' : 'orbit-ring'}
              counterClass={reducedMotion ? '' : 'orbit-item'}
            />

            {/* Middle Ring: r=200, reversed */}
            <OrbitalRing
              items={MIDDLE_RING}
              radius={200}
              ringClass={reducedMotion ? '' : 'orbit-ring-reverse'}
              counterClass={reducedMotion ? '' : 'orbit-item-reverse'}
            />

            {/* Outer Ring: r=270 */}
            <OrbitalRing
              items={OUTER_RING}
              radius={270}
              ringClass={
                reducedMotion
                  ? ''
                  : 'orbit-ring'
              }
              counterClass={reducedMotion ? '' : 'orbit-item'}
            />
          </div>
        </div>

        {/* ── Mobile Grid ── */}
        <div className="md:hidden grid grid-cols-3 gap-3">
          {allTech.map((item) => (
            <TechBadge key={item.name} item={item} />
          ))}
        </div>
      </div>
    </section>
  );
}
