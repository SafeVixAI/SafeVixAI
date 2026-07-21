'use client';

// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
import React from 'react';


import { useRef } from 'react';
import { useGSAP } from '@gsap/react';
import { gsap } from '@/lib/gsap';
import { useScrollReveal } from '../hooks/useLandingGSAP';

/* ═══════════════════════════════════════════════════════════
   CommandCenter — Live Intelligence Dashboard Simulation
   ═══════════════════════════════════════════════════════════ */

// ── Incident data ──────────────────────────────────────────
interface Incident {
  severity: 'P0' | 'P1' | 'P2';
  type: string;
  location: string;
  time: string;
}

const INCIDENTS: Incident[] = [
  { severity: 'P0', type: 'Vehicle Collision', location: 'NH-44, Hyderabad', time: '2m ago' },
  { severity: 'P1', type: 'SOS Alert', location: 'MG Road, Bengaluru', time: '5m ago' },
  { severity: 'P0', type: 'Road Hazard', location: 'NH-48, Pune', time: '8m ago' },
  { severity: 'P2', type: 'Traffic Congestion', location: 'Ring Road, Delhi', time: '12m ago' },
  { severity: 'P1', type: 'Medical Emergency', location: 'ECR, Chennai', time: '18m ago' },
];

const SEVERITY_COLOR: Record<Incident['severity'], string> = {
  P0: '#DC2626',
  P1: '#D97706',
  P2: '#3B82F6',
};

// ── Bar chart data ─────────────────────────────────────────
const BAR_DATA = [
  { day: 'Mon', pct: 60 },
  { day: 'Tue', pct: 80 },
  { day: 'Wed', pct: 45 },
  { day: 'Thu', pct: 90 },
  { day: 'Fri', pct: 70 },
  { day: 'Sat', pct: 55 },
];

// ── City dots for India map ────────────────────────────────
interface CityDot {
  name: string;
  cx: number;
  cy: number;
  color: string;
  pulse: boolean;
}

const CITY_DOTS: CityDot[] = [
  { name: 'Delhi', cx: 195, cy: 145, color: '#DC2626', pulse: true },
  { name: 'Mumbai', cx: 130, cy: 290, color: '#D97706', pulse: false },
  { name: 'Bengaluru', cx: 175, cy: 385, color: '#00C896', pulse: true },
  { name: 'Chennai', cx: 215, cy: 375, color: '#3B82F6', pulse: false },
  { name: 'Kolkata', cx: 285, cy: 230, color: '#DC2626', pulse: true },
  { name: 'Hyderabad', cx: 190, cy: 325, color: '#D97706', pulse: false },
  { name: 'Ahmedabad', cx: 115, cy: 225, color: '#00C896', pulse: false },
  { name: 'Jaipur', cx: 155, cy: 175, color: '#3B82F6', pulse: true },
  { name: 'Lucknow', cx: 225, cy: 180, color: '#DC2626', pulse: false },
  { name: 'Kochi', cx: 165, cy: 420, color: '#00C896', pulse: false },
];

// ── Simplified India SVG outline path ──────────────────────
const INDIA_PATH = `
  M 190 50 
  C 200 55, 220 60, 230 70 
  C 240 80, 260 85, 275 95 
  C 290 105, 305 120, 310 140 
  C 315 160, 320 180, 315 200 
  C 310 215, 305 225, 300 240 
  C 295 255, 290 260, 285 265 
  C 280 270, 278 275, 275 280 
  C 265 295, 255 305, 250 315 
  C 245 325, 240 340, 235 355 
  C 230 370, 225 380, 220 395 
  C 215 410, 210 420, 200 435 
  C 190 450, 180 455, 170 445 
  C 165 440, 160 430, 155 415 
  C 150 400, 148 390, 145 375 
  C 140 355, 138 345, 140 330 
  C 142 315, 135 305, 125 295 
  C 115 285, 108 275, 100 260 
  C 92 245, 88 235, 85 220 
  C 82 205, 85 190, 90 175 
  C 95 160, 100 150, 110 140 
  C 120 130, 125 120, 135 110 
  C 145 100, 150 90, 160 80 
  C 170 70, 175 60, 180 55 
  C 185 50, 188 48, 190 50 Z
`;

// ── Stat pills ─────────────────────────────────────────────
const STAT_PILLS = [
  { label: 'Active', value: '47', color: '#DC2626', bg: 'rgba(220,38,38,0.12)' },
  { label: 'Resolved', value: '312', color: '#00C896', bg: 'rgba(0,200,150,0.12)' },
  { label: 'Monitoring', value: '1,247', color: '#3B82F6', bg: 'rgba(59,130,246,0.12)' },
  { label: 'Response', value: '4.2m', color: '#D97706', bg: 'rgba(217,119,6,0.12)' },
];

// ── AI Alerts ──────────────────────────────────────────────
const AI_ALERTS = [
  { text: 'Pattern detected: NH-44 corridor', severity: 'high' as const },
  { text: 'Anomaly flagged: Ring Road congestion', severity: 'medium' as const },
  { text: 'Predictive alert: Weekend surge area', severity: 'low' as const },
];

export default function CommandCenter() {
  const sectionRef = useScrollReveal({ y: 30, stagger: 0.08, start: 'top 80%' });
  const barsRef = useRef<HTMLDivElement>(null);
  const severityRef = useRef<HTMLDivElement>(null);

  // ── Animate bar chart heights on scroll ──────────────────
  useGSAP(
    () => {
      if (!barsRef.current) return;
      const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
      const bars = barsRef.current.querySelectorAll<HTMLElement>('.bar-fill');
      if (bars.length === 0) return;

      if (prefersReducedMotion) {
        bars.forEach((bar) => {
          bar.style.height = bar.dataset.height ?? '0%';
        });
        return;
      }

      gsap.fromTo(
        bars,
        { height: '0%' },
        {
          height: (i: number) => bars[i].dataset.height ?? '0%',
          duration: 1,
          stagger: 0.08,
          ease: 'power3.out',
          scrollTrigger: {
            trigger: barsRef.current,
            start: 'top 85%',
            toggleActions: 'play none none none',
          },
        }
      );
    },
    { scope: barsRef }
  );

  // ── Animate severity bars on scroll ──────────────────────
  useGSAP(
    () => {
      if (!severityRef.current) return;
      const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
      const fills = severityRef.current.querySelectorAll<HTMLElement>('.severity-fill');
      if (fills.length === 0) return;

      if (prefersReducedMotion) {
        fills.forEach((fill) => {
          fill.style.width = fill.dataset.width ?? '0%';
        });
        return;
      }

      gsap.fromTo(
        fills,
        { width: '0%' },
        {
          width: (i: number) => fills[i].dataset.width ?? '0%',
          duration: 1.2,
          stagger: 0.12,
          ease: 'power3.out',
          scrollTrigger: {
            trigger: severityRef.current,
            start: 'top 85%',
            toggleActions: 'play none none none',
          },
        }
      );
    },
    { scope: severityRef }
  );

  return (
    <section
      id="command-center"
      className="landing-section bg-bg grid-pattern-dense"
      ref={sectionRef}
    >
      <div className="landing-container relative z-10">
        {/* ── Section Header ────────────────────────────── */}
        <div className="text-center mb-16 reveal-item">
          <p className="sv-terminal-overline mb-3">LIVE INTELLIGENCE</p>
          <h2 className="font-space text-3xl lg:text-4xl font-bold text-text-1 mb-4">
            Command Center
          </h2>
          <p className="text-text-2 max-w-2xl mx-auto text-body leading-relaxed">
            Real-time national operations dashboard powering India&apos;s road safety intelligence
            with AI-driven incident monitoring, analytics, and predictive insights.
          </p>
        </div>

        {/* ── Dashboard Mockup ──────────────────────────── */}
        <div className="reveal-item rounded-2xl border border-white/[0.06] bg-surface-1/50 backdrop-blur-sm overflow-hidden p-1 shadow-modal max-w-[1200px] mx-auto">
          <div className="bg-bg rounded-xl overflow-hidden relative">
            {/* Scan line overlay */}
            <div
              className="absolute inset-0 pointer-events-none z-30 overflow-hidden rounded-xl"
              aria-hidden="true"
            >
              <div
                className="absolute left-0 right-0 h-[1px] bg-gradient-to-r from-transparent via-brand-light/20 to-transparent"
                style={{ animation: 'scan-line-move 4s linear infinite', top: '0%' }}
              />
            </div>

            {/* ── Title Bar ─────────────────────────────── */}
            <div className="h-10 bg-surface-1 border-b border-white/[0.06] flex items-center px-4">
              {/* Traffic light dots */}
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-full bg-[#FF5F57]" />
                <span className="w-3 h-3 rounded-full bg-[#FEBC2E]" />
                <span className="w-3 h-3 rounded-full bg-[#28C840]" />
              </div>

              {/* Center title */}
              <span className="flex-1 text-center text-xs font-mono text-text-3">
                SafeVixAI Command Center
              </span>

              {/* LIVE badge */}
              <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emergency/10 border border-emergency/20">
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emergency opacity-75" />
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-emergency" />
                </span>
                <span className="text-[10px] font-mono font-semibold tracking-wider text-emergency uppercase">
                  Live
                </span>
              </div>
            </div>

            {/* ── Content Grid ──────────────────────────── */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-px bg-white/[0.04]">
              {/* ── Left Panel — Active Incidents ──────── */}
              <div className="lg:col-span-3 bg-bg p-4">
                <p className="sv-terminal-overline text-[10px] mb-3 text-text-3">
                  ACTIVE INCIDENTS
                </p>

                <div className="space-y-0">
                  {INCIDENTS.map((inc, i) => (
                    <div
                      key={i}
                      className="py-2.5 border-b border-white/[0.04] last:border-b-0 group"
                    >
                      <div className="flex items-start gap-2.5">
                        {/* Severity dot */}
                        <span
                          className="mt-1.5 w-2 h-2 rounded-full flex-shrink-0"
                          style={{ backgroundColor: SEVERITY_COLOR[inc.severity] }}
                        />
                        <div className="min-w-0 flex-1">
                          <div className="flex items-center justify-between gap-2">
                            <span className="text-xs font-medium text-text-1 truncate">
                              {inc.type}
                            </span>
                            <span
                              className="text-[10px] font-mono px-1.5 py-0.5 rounded text-text-3 flex-shrink-0"
                              style={{
                                backgroundColor: `${SEVERITY_COLOR[inc.severity]}15`,
                                color: SEVERITY_COLOR[inc.severity],
                              }}
                            >
                              {inc.severity}
                            </span>
                          </div>
                          <p className="text-xs text-text-3 font-mono mt-0.5 truncate">
                            {inc.location}
                          </p>
                          <p className="text-[10px] text-text-3/60 mt-0.5">{inc.time}</p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* ── Center Panel — National Overview ──── */}
              <div className="lg:col-span-6 bg-bg p-4">
                <p className="sv-terminal-overline text-[10px] mb-3 text-text-3">
                  NATIONAL OVERVIEW
                </p>

                {/* India SVG Map */}
                <div className="relative flex justify-center">
                  <svg
                    viewBox="0 0 400 500"
                    className="w-full max-w-[340px] h-auto"
                    aria-label="Map of India showing incident locations"
                    role="img"
                  >
                    {/* Country outline */}
                    <path
                      d={INDIA_PATH}
                      fill="none"
                      stroke="rgba(255,255,255,0.08)"
                      strokeWidth="1.5"
                      className="drop-shadow-sm"
                    />
                    <path
                      d={INDIA_PATH}
                      fill="rgba(0,200,150,0.03)"
                      stroke="none"
                    />

                    {/* City markers with pulse rings */}
                    {CITY_DOTS.map((city) => (
                      <g key={city.name}>
                        {/* Pulse ring for pulsing cities */}
                        {city.pulse && (
                          <circle
                            cx={city.cx}
                            cy={city.cy}
                            r="8"
                            fill="none"
                            stroke={city.color}
                            strokeWidth="0.8"
                            opacity="0.5"
                          >
                            <animate
                              attributeName="r"
                              from="4"
                              to="16"
                              dur="2s"
                              repeatCount="indefinite"
                            />
                            <animate
                              attributeName="opacity"
                              from="0.6"
                              to="0"
                              dur="2s"
                              repeatCount="indefinite"
                            />
                          </circle>
                        )}

                        {/* Outer glow */}
                        <circle
                          cx={city.cx}
                          cy={city.cy}
                          r="6"
                          fill={city.color}
                          opacity="0.15"
                        />

                        {/* Dot */}
                        <circle
                          cx={city.cx}
                          cy={city.cy}
                          r="3"
                          fill={city.color}
                        />

                        {/* City label */}
                        <text
                          x={city.cx + 8}
                          y={city.cy + 3}
                          fill="rgba(255,255,255,0.35)"
                          fontSize="8"
                          fontFamily="var(--font-mono)"
                        >
                          {city.name}
                        </text>
                      </g>
                    ))}
                  </svg>
                </div>

                {/* Stat pills */}
                <div className="flex flex-wrap items-center justify-center gap-2 mt-4">
                  {STAT_PILLS.map((pill) => (
                    <div
                      key={pill.label}
                      className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-mono"
                      style={{
                        backgroundColor: pill.bg,
                        color: pill.color,
                        border: `1px solid ${pill.color}20`,
                      }}
                    >
                      <span
                        className="w-1.5 h-1.5 rounded-full"
                        style={{ backgroundColor: pill.color }}
                      />
                      {pill.label}: {pill.value}
                    </div>
                  ))}
                </div>
              </div>

              {/* ── Right Panel — Analytics ─────────────── */}
              <div className="lg:col-span-3 bg-bg p-4">
                <p className="sv-terminal-overline text-[10px] mb-3 text-text-3">ANALYTICS</p>

                {/* Bar Chart */}
                <div ref={barsRef} className="flex items-end gap-1.5 h-28 mb-3">
                  {BAR_DATA.map((bar) => (
                    <div key={bar.day} className="flex-1 flex flex-col items-center gap-1">
                      <div className="w-full relative h-full flex items-end">
                        <div
                          className="bar-fill w-full rounded-t"
                          data-height={`${bar.pct}%`}
                          style={{
                            height: '0%',
                            background: `linear-gradient(to top, var(--brand), var(--brand-light))`,
                          }}
                        />
                      </div>
                      <span className="text-[9px] text-text-3 font-mono">{bar.day}</span>
                    </div>
                  ))}
                </div>

                {/* Severity Distribution */}
                <div ref={severityRef}>
                  <p className="text-[10px] font-mono text-text-3 uppercase tracking-wider mb-2 mt-4">
                    Severity Distribution
                  </p>
                  {[
                    { label: 'P0 Critical', pct: 30, color: '#DC2626' },
                    { label: 'P1 High', pct: 45, color: '#D97706' },
                    { label: 'P2 Medium', pct: 25, color: '#3B82F6' },
                  ].map((sev) => (
                    <div key={sev.label} className="mb-2">
                      <div className="flex justify-between text-[10px] mb-1">
                        <span className="text-text-2">{sev.label}</span>
                        <span className="text-text-3 font-mono">{sev.pct}%</span>
                      </div>
                      <div className="h-1.5 rounded-full bg-white/[0.04] overflow-hidden">
                        <div
                          className="severity-fill h-full rounded-full"
                          data-width={`${sev.pct}%`}
                          style={{
                            width: '0%',
                            backgroundColor: sev.color,
                          }}
                        />
                      </div>
                    </div>
                  ))}
                </div>

                {/* AI Alerts */}
                <p className="text-[10px] font-mono text-text-3 uppercase tracking-wider mb-2 mt-4">
                  AI Alerts
                </p>
                <div className="space-y-1.5">
                  {AI_ALERTS.map((alert, idx) => (
                    <div
                      key={idx}
                      className="flex items-start gap-2 p-2 rounded-md bg-white/[0.02] border border-white/[0.04]"
                    >
                      <span
                        className="mt-1 w-1.5 h-1.5 rounded-full flex-shrink-0"
                        style={{
                          backgroundColor:
                            alert.severity === 'high'
                              ? '#DC2626'
                              : alert.severity === 'medium'
                                ? '#D97706'
                                : '#3B82F6',
                        }}
                      />
                      <span className="text-[10px] text-text-2 leading-snug">{alert.text}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}