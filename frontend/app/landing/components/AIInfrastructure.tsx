'use client';

// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
import React, { useRef, useState, useEffect } from 'react';
import { useGSAP } from '@gsap/react';
import { gsap } from '@/lib/gsap';

import { useScrollReveal } from '../hooks/useLandingGSAP';
import { Database, Cpu, Brain, Siren, BarChart3, type LucideIcon } from 'lucide-react';

/* ═══════════════════════════════════════════════════════════
   AIInfrastructure — Intelligence Pipeline Flow Diagram
   ═══════════════════════════════════════════════════════════ */

// ── Pipeline nodes ─────────────────────────────────────────
interface PipelineNode {
  id: string;
  title: string;
  description: string;
  icon: LucideIcon;
}

const PIPELINE_NODES: PipelineNode[] = [
  {
    id: 'ingest',
    title: 'Data Ingestion',
    description: 'Multi-source data collection from sensors, reports, and APIs',
    icon: Database,
  },
  {
    id: 'process',
    title: 'AI Processing',
    description: 'Real-time ML inference with Gemini and edge AI models',
    icon: Cpu,
  },
  {
    id: 'predict',
    title: 'Prediction Engine',
    description: 'Predictive risk analysis and pattern recognition',
    icon: Brain,
  },
  {
    id: 'respond',
    title: 'Emergency Response',
    description: 'Automated emergency dispatch and routing optimization',
    icon: Siren,
  },
  {
    id: 'analytics',
    title: 'Analytics',
    description: 'Continuous learning and performance monitoring',
    icon: BarChart3,
  },
];

// ── Connector Arrow (desktop: horizontal, mobile: vertical) ──
function Connector({ index }: { index: number }) {
  return (
    <div className="flex items-center justify-center shrink-0 relative" aria-hidden="true">
      {/* Desktop horizontal connector */}
      <svg
        className="hidden lg:block relative z-0"
        width="64"
        height="24"
        viewBox="0 0 64 24"
        fill="none"
      >
        <line
          x1="0"
          y1="12"
          x2="52"
          y2="12"
          stroke="rgba(0,200,150,0.3)"
          strokeWidth="1.5"
          className="flow-line-animated"
        />
        {/* Arrow head */}
        <path
          d="M52 6 L62 12 L52 18"
          stroke="rgba(0,200,150,0.4)"
          strokeWidth="1.5"
          fill="none"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        {/* Node number */}
        <circle cx="32" cy="12" r="8" fill="var(--surface-2)" stroke="rgba(0,200,150,0.2)" strokeWidth="1" />
        <text x="32" y="16" textAnchor="middle" fill="var(--brand-light)" fontSize="9" fontFamily="var(--font-mono)">
          {index + 1}
        </text>
      </svg>
      
      {/* Data packet animation */}
      <div className="hidden lg:block absolute left-0 top-[11px] w-[52px] h-[2px] z-10 pointer-events-none overflow-visible">
        <div className="data-packet w-1.5 h-1.5 bg-brand-light rounded-full absolute" style={{ boxShadow: '0 0 6px rgba(0,200,150,0.8)' }} />
      </div>

      {/* Mobile vertical connector */}
      <svg
        className="block lg:hidden"
        width="24"
        height="48"
        viewBox="0 0 24 48"
        fill="none"
      >
        <line
          x1="12"
          y1="0"
          x2="12"
          y2="36"
          stroke="rgba(0,200,150,0.3)"
          strokeWidth="1.5"
          className="flow-line-animated"
        />
        <path
          d="M6 36 L12 46 L18 36"
          stroke="rgba(0,200,150,0.4)"
          strokeWidth="1.5"
          fill="none"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    </div>
  );
}

// ── Pipeline Node Card ─────────────────────────────────────
function NodeCard({ node, index, isActive }: { node: PipelineNode; index: number; isActive: boolean }) {
  const Icon = node.icon;

  return (
    <div className={`reveal-item sv-glass glass-shimmer rounded-xl p-6 w-full lg:w-56 flex flex-col items-center text-center group group/node transition-all duration-300 hover:scale-105 hover:z-10 hover:border-brand-light/20 ${isActive ? 'neon-pulse-green border-brand-light/40' : ''}`}>
      {/* Step indicator (mobile) */}
      <div className="lg:hidden absolute -top-3 left-1/2 -translate-x-1/2 w-6 h-6 rounded-full bg-surface-2 border border-brand-light/20 flex items-center justify-center">
        <span className="text-[10px] font-mono text-brand-light">{index + 1}</span>
      </div>

      {/* Icon circle */}
      <div className={`w-12 h-12 rounded-full border flex items-center justify-center transition-colors duration-300 ${isActive ? 'bg-brand/30 border-brand-light/50' : 'bg-brand/10 border-brand-light/20 group-hover/node:bg-brand/20'}`}>
        <Icon size={22} className="text-brand-light" strokeWidth={1.5} />
      </div>

      {/* Title */}
      <h3 className="font-space text-base font-semibold text-text-1 mt-4">
        {node.title}
      </h3>

      {/* Description */}
      <p className="text-xs text-text-3 group-hover/node:text-text-2 transition-colors duration-300 mt-2 leading-relaxed">
        {node.description}
      </p>
    </div>
  );
}

export default function AIInfrastructure() {
  const sectionRef = useScrollReveal({ y: 40, stagger: 0.12, start: 'top 80%' });
  const statsRef = useRef<HTMLDivElement>(null);
  const [activeIndex, setActiveIndex] = useState(-1);

  useEffect(() => {
    const interval = setInterval(() => {
      setActiveIndex(Math.floor(Math.random() * PIPELINE_NODES.length));
    }, 3000);
    return () => clearInterval(interval);
  }, []);

  useGSAP(() => {
    if (!statsRef.current) return;
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (prefersReducedMotion) {
      gsap.set('.stat-counter', { 
        innerText: (i: number, el: HTMLElement) => el.getAttribute('data-value') 
      });
      return;
    }

    gsap.fromTo('.stat-fade', 
      { opacity: 0 },
      { opacity: 1, duration: 1.5, stagger: 0.1, scrollTrigger: { trigger: statsRef.current, start: 'top 85%' } }
    );

    const counterElements = gsap.utils.toArray<HTMLElement>('.stat-counter');
    counterElements.forEach(el => {
      const endValue = parseFloat(el.getAttribute('data-value') || '0');
      const isFloat = endValue % 1 !== 0;
      
      gsap.fromTo(el,
        { innerText: 0 },
        {
          innerText: endValue,
          duration: 2,
          ease: 'power2.out',
          snap: { innerText: isFloat ? 0.01 : 1 },
          scrollTrigger: {
            trigger: statsRef.current,
            start: 'top 85%',
          },
          onUpdate: function() {
            el.innerText = isFloat 
              ? parseFloat(this.targets()[0].innerText).toFixed(2)
              : Math.floor(parseFloat(this.targets()[0].innerText)).toString();
          }
        }
      );
    });
  }, { scope: statsRef });

  return (
    <section
      id="intelligence"
      className="landing-section bg-bg glow-brand-ambient"
      ref={sectionRef}
    >
      <div className="landing-container relative z-10">
        {/* ── Section Header ────────────────────────────── */}
        <div className="text-center mb-16 reveal-item">
          <p className="sv-terminal-overline mb-3">AI INFRASTRUCTURE</p>
          <h2 className="font-space text-3xl lg:text-4xl font-bold text-text-1 mb-4">
            Intelligence Pipeline
          </h2>
          <p className="text-text-2 max-w-2xl mx-auto text-body leading-relaxed">
            From raw sensor data to life-saving decisions in under 4 seconds.
            Our end-to-end AI pipeline processes, predicts, and responds at national scale.
          </p>
        </div>

        {/* ── Flow Diagram ──────────────────────────────── */}
        <div className="reveal-item">
          {/* Desktop: horizontal flow */}
          <div className="hidden lg:flex items-center justify-center gap-0">
            {PIPELINE_NODES.map((node, i) => (
              <div key={node.id} className="flex items-center">
                <NodeCard node={node} index={i} isActive={activeIndex === i} />
                {i < PIPELINE_NODES.length - 1 && <Connector index={i} />}
              </div>
            ))}
          </div>

          {/* Mobile: vertical flow */}
          <div className="flex lg:hidden flex-col items-center gap-0 max-w-xs mx-auto">
            {PIPELINE_NODES.map((node, i) => (
              <div key={node.id} className="flex flex-col items-center relative">
                <NodeCard node={node} index={i} isActive={activeIndex === i} />
                {i < PIPELINE_NODES.length - 1 && <Connector index={i} />}
              </div>
            ))}
          </div>
        </div>

        {/* ── Throughput Stats ───────────────────────────── */}
        <div ref={statsRef} className="reveal-item mt-16 flex flex-wrap items-center justify-center gap-6 lg:gap-12">
          {/* Item 1 */}
          <div className="text-center">
            <p className="counter-number font-space text-2xl font-bold text-brand-light stat-fade">
              &lt;4s
            </p>
            <p className="text-xs text-text-3 font-mono uppercase tracking-wider mt-1">
              Response Time
            </p>
          </div>
          {/* Item 2 */}
          <div className="text-center">
            <p className="counter-number font-space text-2xl font-bold text-brand-light">
              10M+
            </p>
            <p className="text-xs text-text-3 font-mono uppercase tracking-wider mt-1">
              Daily Events
            </p>
          </div>
          {/* Item 3 */}
          <div className="text-center">
            <p className="counter-number font-space text-2xl font-bold text-brand-light">
              99.97%
            </p>
            <p className="text-xs text-text-3 font-mono uppercase tracking-wider mt-1">
              Uptime SLA
            </p>
          </div>
          {/* Item 4 */}
          <div className="text-center">
            <p className="counter-number font-space text-2xl font-bold text-brand-light">
              28
            </p>
            <p className="text-xs text-text-3 font-mono uppercase tracking-wider mt-1">
              State Coverage
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}