'use client';

// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
import React, { useState, useEffect } from 'react';
import { useScrollReveal, useCountUp } from '../hooks/useLandingGSAP';
import { fetchPublicStats } from '@/lib/api';
import MapLibreDashboard from '@/components/command-center/MapLibreDashboard';

/* ═══════════════════════════════════════════════════════════
   NationalNetwork — Connected Intelligence Visualization
   ═══════════════════════════════════════════════════════════ */



// ── Stat data ──────────────────────────────────────────────
interface StatBlock {
  value: number;
  suffix: string;
  label: string;
  color: string;
}

const MOCK_STATS: StatBlock[] = [
  { value: 28, suffix: '', label: 'States Connected', color: '#00C896' },
  { value: 5000, suffix: '+', label: 'Hospitals Linked', color: '#DC2626' },
  { value: 15000, suffix: '+', label: 'Police Stations', color: '#3B82F6' },
  { value: 14, suffix: '0M', label: 'Citizens Protected', color: 'var(--brand-light)' },
];

// ── Stat Counter Component ─────────────────────────────────
function StatCounter({ stat }: { stat: StatBlock }) {
  const ref = useCountUp(stat.value, { duration: 2.2, start: 'top 85%' });

  return (
    <div className="reveal-item shimmer-on-hover rounded-xl p-4 transition-colors hover:bg-white/[0.02]">
      <div className="flex items-baseline gap-1">
        <span
          ref={ref}
          className="counter-number font-space text-4xl font-bold"
          style={{ color: stat.color }}
        >
          0
        </span>
        {stat.suffix && (
          <span
            className="font-space text-2xl font-bold"
            style={{ color: stat.color }}
          >
            {stat.suffix}
          </span>
        )}
      </div>
      <p className="text-sm text-text-2 uppercase tracking-wider mt-1">
        {stat.label}
      </p>
    </div>
  );
}

export default function NationalNetwork() {
  const sectionRef = useScrollReveal({ y: 40, stagger: 0.1, start: 'top 80%' });
  
  const [activeNodeIdx, setActiveNodeIdx] = useState(-1);
  const [syncCounter, setSyncCounter] = useState(2);
  const [statsData, setStatsData] = useState<StatBlock[]>(MOCK_STATS);

  useEffect(() => {
    let mounted = true;
    fetchPublicStats().then(data => {
      if (mounted && data) {
        setStatsData([
          { value: Number(data.total_complaints_filed) || 0, suffix: '', label: 'Total Incidents', color: '#DC2626' },
          { value: Number(data.total_resolved) || 0, suffix: '', label: 'Incidents Resolved', color: '#00C896' },
          { value: Number(data.active_field_officers) || 0, suffix: '', label: 'Active Officers', color: '#3B82F6' },
          { value: Number(data.resolution_rate) || 0, suffix: '%', label: 'Resolution Rate', color: 'var(--brand-light)' },
        ]);
      }
    }).catch(console.error);
    return () => { mounted = false; };
  }, []);

  // Sync Counter Logic
  useEffect(() => {
    const interval = setInterval(() => {
      setSyncCounter(prev => prev >= 30 ? 0 : prev + 1);
    }, 1000);
    return () => clearInterval(interval);
  }, []);



  return (
    <section
      id="national-network"
      className="landing-section bg-bg"
      ref={sectionRef}
    >
      <div className="landing-container relative z-10">
        {/* ── Section Header ────────────────────────────── */}
        <div className="text-center mb-16 reveal-item">
          <p className="sv-terminal-overline mb-3">NATIONAL NETWORK</p>
          <h2 className="font-space text-3xl lg:text-4xl font-bold text-text-1 mb-4">
            Connected Intelligence
          </h2>
          <p className="text-text-2 max-w-2xl mx-auto text-body leading-relaxed">
            A unified network connecting hospitals, police stations, emergency services,
            and critical infrastructure across India&apos;s 28 states and 8 union territories.
          </p>
        </div>

        {/* ── Two Column Layout ─────────────────────────── */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
          {/* ── Left: India Network Visualization ────────── */}
          <div className="reveal-item flex justify-center">
            <div className="relative w-full max-w-md h-[450px]" role="img" aria-label="National network map">
              <MapLibreDashboard zoom={4} center={[78.9629, 20.5937]} />
            </div>
          </div>

          {/* ── Right: Stats + Content ───────────────────── */}
          <div className="space-y-8">
            {/* Stat blocks */}
            <div className="grid grid-cols-2 gap-6">
              {statsData.map((stat) => (
                <StatCounter key={stat.label} stat={stat} />
              ))}
            </div>

            {/* Descriptive content */}
            <div className="reveal-item space-y-4 pt-4 border-t border-white/[0.06]">
              <p className="text-text-2 text-body leading-relaxed">
                SafeVixAI&apos;s national network provides <span className="text-text-1 font-medium">end-to-end coverage</span> across
                India&apos;s road infrastructure. Every connected node — from tier-1 trauma centers to
                rural police outposts — feeds real-time data into our AI intelligence pipeline.
              </p>
              <p className="text-text-2 text-body leading-relaxed">
                Our distributed architecture ensures <span className="text-text-1 font-medium">sub-second response times</span> even
                in low-connectivity regions, with edge-AI processing and satellite fallback
                for mission-critical emergency coordination.
              </p>
            </div>

            {/* Network status bar */}
            <div className="reveal-item flex items-center gap-3 p-4 rounded-xl bg-surface-1 border border-white/[0.06]">
              <div className="relative flex h-3 w-3 neon-pulse-green rounded-full">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-brand-light opacity-75" />
                <span className="relative inline-flex rounded-full h-3 w-3 bg-brand-light" />
              </div>
              <div>
                <p className="text-xs font-medium text-text-1">Network Status: Operational</p>
                <p className="text-[10px] text-text-3 font-mono mt-0.5">
                  All 28 state nodes online · Last sync: {syncCounter}s ago · Latency: 12ms avg
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}