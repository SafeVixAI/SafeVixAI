'use client';

// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
import React, { useState, useEffect } from 'react';
import { useRef } from 'react';
import { useGSAP } from '@gsap/react';
import { gsap } from '@/lib/gsap';
import { useScrollReveal, useCountUp } from '../hooks/useLandingGSAP';

/* ═══════════════════════════════════════════════════════════
   NationalNetwork — Connected Intelligence Visualization
   ═══════════════════════════════════════════════════════════ */

// ── India outline (simplified, larger) ─────────────────────
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

const STATS: StatBlock[] = [
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
            <div className="relative w-full max-w-md">
              <svg
                ref={svgRef}
                viewBox="0 0 400 500"
                className="w-full h-auto"
                aria-label="National network map showing connected nodes across India"
                role="img"
              >
                {/* Background glow */}
                <defs>
                  <radialGradient id="map-glow" cx="50%" cy="50%" r="50%">
                    <stop offset="0%" stopColor="rgba(0,200,150,0.06)" />
                    <stop offset="100%" stopColor="transparent" />
                  </radialGradient>
                </defs>
                <rect width="400" height="500" fill="url(#map-glow)" />

                {/* Country outline */}
                <path
                  d={INDIA_PATH}
                  fill="rgba(0,200,150,0.02)"
                  stroke="rgba(255,255,255,0.1)"
                  strokeWidth="1.5"
                />

                {/* Connection lines */}
                {connections.map((line, i) => (
                  <line
                    key={`conn-${i}`}
                    x1={line.x1}
                    y1={line.y1}
                    x2={line.x2}
                    y2={line.y2}
                    stroke="rgba(0,200,150,0.12)"
                    strokeWidth="0.8"
                    className="network-line"
                  />
                ))}

                {/* Data flow dots */}
                {dataFlowConnections.map((line, i) => (
                  <circle key={`flow-${i}`} cx={line.x1} cy={line.y1} r="2" fill="var(--brand-light)">
                    <animate attributeName="cx" values={`${line.x1};${line.x2}`} dur={`${2 + (i % 3) * 0.5}s`} repeatCount="indefinite" begin={`${i * 0.4}s`} />
                    <animate attributeName="cy" values={`${line.y1};${line.y2}`} dur={`${2 + (i % 3) * 0.5}s`} repeatCount="indefinite" begin={`${i * 0.4}s`} />
                    <animate attributeName="opacity" values="0;1;1;0" dur={`${2 + (i % 3) * 0.5}s`} repeatCount="indefinite" begin={`${i * 0.4}s`} />
                  </circle>
                ))}

                {/* Network nodes */}
                {NETWORK_NODES.map((node, i) => {
                  const color = NODE_COLORS[node.type];
                  return (
                    <g key={`node-${i}`}>
                      {/* Random activity pulse */}
                      {activeNodeIdx === i && (
                        <circle cx={node.cx} cy={node.cy} r="6" fill="none" stroke={color} strokeWidth="1.5">
                          <animate attributeName="r" from="6" to="24" dur="1.5s" fill="freeze" />
                          <animate attributeName="opacity" from="0.8" to="0" dur="1.5s" fill="freeze" />
                        </circle>
                      )}

                      {/* Pulse ring */}
                      {node.pulse && (
                        <circle
                          cx={node.cx}
                          cy={node.cy}
                          r="4"
                          fill="none"
                          stroke={color}
                          strokeWidth="0.6"
                        >
                          <animate
                            attributeName="r"
                            from="4"
                            to="14"
                            dur="2.5s"
                            repeatCount="indefinite"
                          />
                          <animate
                            attributeName="opacity"
                            from="0.5"
                            to="0"
                            dur="2.5s"
                            repeatCount="indefinite"
                          />
                        </circle>
                      )}

                      {/* Outer glow */}
                      <circle
                        cx={node.cx}
                        cy={node.cy}
                        r="5"
                        fill={color}
                        opacity="0.15"
                      />

                      {/* Core dot */}
                      <circle
                        cx={node.cx}
                        cy={node.cy}
                        r="2.5"
                        fill={color}
                      />
                    </g>
                  );
                })}
              </svg>

              {/* Legend */}
              <div className="flex flex-wrap items-center justify-center gap-x-5 gap-y-2 mt-4">
                {(Object.entries(NODE_LABELS) as [NodeType, string][]).map(([type, label]) => (
                  <div key={type} className="flex items-center gap-1.5">
                    <span
                      className="w-2.5 h-2.5 rounded-full"
                      style={{ backgroundColor: NODE_COLORS[type] }}
                    />
                    <span className="text-xs text-text-3 font-mono">{label}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* ── Right: Stats + Content ───────────────────── */}
          <div className="space-y-8">
            {/* Stat blocks */}
            <div className="grid grid-cols-2 gap-6">
              {STATS.map((stat) => (
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