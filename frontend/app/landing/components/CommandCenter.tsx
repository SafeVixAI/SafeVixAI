'use client';

// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
import React from 'react';


import { useRef, useState, useEffect } from 'react';
import { useGSAP } from '@gsap/react';
import { gsap } from '@/lib/gsap';
import { useScrollReveal } from '../hooks/useLandingGSAP';
import IntelligenceGlobe from './three/IntelligenceGlobe';

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
  const [activeIncidentIdx, setActiveIncidentIdx] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setActiveIncidentIdx((prev) => (prev + 1) % INCIDENTS.length);
    }, 4000);
    return () => clearInterval(interval);
  }, []);

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
        <div className="reveal-item glass-shimmer rounded-2xl border border-white/[0.06] bg-surface-1/50 backdrop-blur-sm overflow-hidden p-1 shadow-modal max-w-[1200px] mx-auto">
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
              <div className="neon-pulse-green rounded-full">
                <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emergency/10 border border-emergency/20">
                  <span className="relative flex h-2.5 w-2.5">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emergency opacity-75" />
                    <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emergency" />
                  </span>
                  <span className="text-[10px] font-mono font-semibold tracking-wider text-emergency uppercase">
                    Live
                  </span>
                </div>
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
                      className={`py-2.5 px-2 -mx-2 rounded border-b border-white/[0.04] last:border-b-0 group transition-colors duration-300 ${
                        i === activeIncidentIdx ? 'bg-white/[0.04] incident-flash' : ''
                      }`}
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

                {/* 3D Intelligence Globe */}
                <div 
                  className="relative flex justify-center h-[350px] md:h-[400px]"
                  role="img"
                  aria-label="India SVG map"
                >
                  <IntelligenceGlobe />
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
                          className="bar-fill w-full rounded-t hover:scale-x-110 hover:brightness-110 transition-all duration-200 cursor-pointer"
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
                <div ref={severityRef} className="shimmer-auto">
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
                      className="flex items-start gap-2 p-2 rounded-md bg-white/[0.02] border border-white/[0.04] border-l-2"
                      style={{
                        borderLeftColor:
                          alert.severity === 'high'
                            ? '#DC2626'
                            : alert.severity === 'medium'
                              ? '#D97706'
                              : '#3B82F6',
                      }}
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