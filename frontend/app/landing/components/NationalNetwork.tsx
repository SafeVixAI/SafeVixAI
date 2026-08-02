'use client';

// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
import React, { useState, useEffect } from 'react';
import { useRef } from 'react';
import { useGSAP } from '@gsap/react';
import { gsap } from '@/lib/gsap';
import { useScrollReveal, useCountUp } from '../hooks/useLandingGSAP';
import { fetchPublicStats } from '@/lib/api';
import MapLibreDashboard from '@/components/command-center/MapLibreDashboard';

/* ═══════════════════════════════════════════════════════════
   NationalNetwork — Connected Intelligence Visualization
   ═══════════════════════════════════════════════════════════ */

// ── India outline (geographically accurate silhouette for 400x500 viewBox) ──
const INDIA_PATH = `
  M 175 42
  C 185 38, 195 40, 205 48
  C 215 55, 222 62, 218 75
  C 214 88, 220 98, 232 108
  C 244 118, 258 128, 272 138
  C 285 145, 292 142, 305 145
  C 318 148, 332 152, 342 165
  C 352 178, 348 195, 338 210
  C 328 222, 318 228, 305 220
  C 294 214, 288 218, 280 228
  C 274 238, 268 252, 262 268
  C 256 284, 248 302, 240 322
  C 232 342, 226 365, 218 388
  C 210 410, 200 430, 186 448
  C 180 455, 174 452, 168 440
  C 160 422, 154 402, 146 380
  C 138 358, 132 332, 126 305
  C 120 280, 110 268, 98 258
  C 88 248, 84 235, 86 222
  C 88 208, 98 205, 110 198
  C 122 190, 130 178, 140 160
  C 150 142, 158 120, 162 98
  C 166 76, 170 55, 175 42 Z
`;

// ── Network node types ─────────────────────────────────────
type NodeType = 'hospital' | 'police' | 'emergency' | 'infrastructure';

interface NetworkNode {
  cx: number;
  cy: number;
  type: NodeType;
  pulse?: boolean;
}

const NODE_COLORS: Record<NodeType, string> = {
  hospital: '#DC2626',
  police: '#3B82F6',
  emergency: '#D97706',
  infrastructure: '#00C896',
};

const NODE_LABELS: Record<NodeType, string> = {
  hospital: 'Hospitals',
  police: 'Police',
  emergency: 'Emergency',
  infrastructure: 'Infrastructure',
};

// ── Node positions across India ────────────────────────────
const NETWORK_NODES: NetworkNode[] = [
  // Hospitals (red)
  { cx: 195, cy: 145, type: 'hospital', pulse: true },
  { cx: 130, cy: 290, type: 'hospital' },
  { cx: 175, cy: 385, type: 'hospital', pulse: true },
  { cx: 285, cy: 230, type: 'hospital' },
  { cx: 225, cy: 180, type: 'hospital' },
  { cx: 155, cy: 415, type: 'hospital' },
  { cx: 250, cy: 160, type: 'hospital' },
  { cx: 200, cy: 330, type: 'hospital', pulse: true },
  // Police (blue)
  { cx: 215, cy: 375, type: 'police' },
  { cx: 155, cy: 175, type: 'police', pulse: true },
  { cx: 190, cy: 250, type: 'police' },
  { cx: 270, cy: 200, type: 'police' },
  { cx: 145, cy: 340, type: 'police' },
  { cx: 230, cy: 290, type: 'police', pulse: true },
  // Emergency (amber)
  { cx: 165, cy: 210, type: 'emergency', pulse: true },
  { cx: 240, cy: 310, type: 'emergency' },
  { cx: 120, cy: 250, type: 'emergency' },
  { cx: 205, cy: 400, type: 'emergency', pulse: true },
  // Infrastructure (green)
  { cx: 180, cy: 125, type: 'infrastructure' },
  { cx: 115, cy: 225, type: 'infrastructure', pulse: true },
  { cx: 260, cy: 270, type: 'infrastructure' },
  { cx: 195, cy: 355, type: 'infrastructure' },
  { cx: 300, cy: 180, type: 'infrastructure', pulse: true },
];

// ── Connection lines between nearby nodes ──────────────────
interface ConnectionLine {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
}

function generateConnections(nodes: NetworkNode[], maxDist: number): ConnectionLine[] {
  const lines: ConnectionLine[] = [];
  for (let i = 0; i < nodes.length; i++) {
    for (let j = i + 1; j < nodes.length; j++) {
      const dx = nodes[i].cx - nodes[j].cx;
      const dy = nodes[i].cy - nodes[j].cy;
      const dist = Math.sqrt(dx * dx + dy * dy);
      if (dist < maxDist && nodes[i].type !== nodes[j].type) {
        lines.push({
          x1: nodes[i].cx,
          y1: nodes[i].cy,
          x2: nodes[j].cx,
          y2: nodes[j].cy,
        });
      }
    }
  }
  return lines;
}

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
  const connections = generateConnections(NETWORK_NODES, 80);
  const svgRef = useRef<SVGSVGElement>(null);
  
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

  // Random Activity Pulse Logic
  useEffect(() => {
    const interval = setInterval(() => {
      setActiveNodeIdx(Math.floor(Math.random() * NETWORK_NODES.length));
      setTimeout(() => setActiveNodeIdx(-1), 1500);
    }, 2500);
    return () => clearInterval(interval);
  }, []);

  // Animate connection lines drawing on scroll
  useGSAP(
    () => {
      if (!svgRef.current) return;
      const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
      if (prefersReducedMotion) return;

      const lines = svgRef.current.querySelectorAll<SVGLineElement>('.network-line');
      lines.forEach((line) => {
        const length = Math.sqrt(
          Math.pow(Number(line.getAttribute('x2')) - Number(line.getAttribute('x1')), 2) +
          Math.pow(Number(line.getAttribute('y2')) - Number(line.getAttribute('y1')), 2)
        );
        line.style.strokeDasharray = `${length}`;
        line.style.strokeDashoffset = `${length}`;

        gsap.to(line, {
          strokeDashoffset: 0,
          duration: 1.5,
          ease: 'power2.out',
          scrollTrigger: {
            trigger: svgRef.current,
            start: 'top 80%',
            toggleActions: 'play none none none',
          },
        });
      });
    },
    { scope: svgRef }
  );

  // Extract subset of connections for data flow dots
  const dataFlowConnections = connections
    .filter(line => 
      NETWORK_NODES.some(n => n.pulse && ((n.cx === line.x1 && n.cy === line.y1) || (n.cx === line.x2 && n.cy === line.y2)))
    )
    .slice(0, 6); // Add up to 6 traveling dots

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