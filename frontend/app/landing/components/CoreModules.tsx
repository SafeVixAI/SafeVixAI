'use client';

// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
import React from 'react';


import { useRef, useState, useCallback } from 'react';
import { gsap } from '@/lib/gsap';
import { useScrollReveal } from '../hooks/useLandingGSAP';
import {
  Shield,
  Scale,
  Eye,
  ArrowRight,
  type LucideIcon,
} from 'lucide-react';

/* ═══════════════════════════════════════════════════════
   MODULE DATA
   ═══════════════════════════════════════════════════════ */

interface ModuleData {
  name: string;
  tagline: string;
  icon: LucideIcon;
  color: string;
  glowClass: string;
  features: string[];
}

const MODULES: ModuleData[] = [
  {
    name: 'RoadSOS',
    tagline: 'AI-Powered Emergency Response',
    icon: Shield,
    color: '#DC2626',
    glowClass: 'module-glow-sos',
    features: [
      'AI Crash Detection',
      'SOS Activation',
      'Emergency Routing',
      'Hospital Communication',
      'Family Live Tracking',
    ],
  },
  {
    name: 'DriveLegal',
    tagline: 'Intelligent Challan Management',
    icon: Scale,
    color: '#00C896',
    glowClass: 'module-glow-legal',
    features: [
      'Challan Intelligence',
      'Fine Analysis',
      'Legal Guidance',
      'Motor Vehicle Act',
      'Penalty Calculator',
    ],
  },
  {
    name: 'RoadWatch',
    tagline: 'Crowd-Powered Hazard Intelligence',
    icon: Eye,
    color: '#D97706',
    glowClass: 'module-glow-watch',
    features: [
      'Hazard Reporting',
      'Crowd Intelligence',
      'Road Condition Monitoring',
      'Infrastructure Awareness',
      'Pothole Detection',
    ],
  },
];

/* ═══════════════════════════════════════════════════════
   3D Tilt Module Card
   ═══════════════════════════════════════════════════════ */

function ModuleCard({ module }: { module: ModuleData }) {
  const cardRef = useRef<HTMLDivElement>(null);
  const innerRef = useRef<HTMLDivElement>(null);
  const [isHovered, setIsHovered] = useState(false);
  const Icon = module.icon;

  const handleMouseMove = useCallback(
    (e: React.MouseEvent<HTMLDivElement>) => {
      if (!cardRef.current || !innerRef.current) return;

      const prefersReducedMotion = window.matchMedia(
        '(prefers-reduced-motion: reduce)'
      ).matches;
      if (prefersReducedMotion) return;

      const rect = cardRef.current.getBoundingClientRect();
      const centerX = rect.left + rect.width / 2;
      const centerY = rect.top + rect.height / 2;
      const mouseX = e.clientX - centerX;
      const mouseY = e.clientY - centerY;

      const rotateY = (mouseX / (rect.width / 2)) * 8;
      const rotateX = -(mouseY / (rect.height / 2)) * 8;

      gsap.to(innerRef.current, {
        rotateX,
        rotateY,
        duration: 0.4,
        ease: 'power2.out',
        overwrite: 'auto',
      });
    },
    []
  );

  const handleMouseLeave = useCallback(() => {
    if (!innerRef.current) return;
    setIsHovered(false);

    gsap.to(innerRef.current, {
      rotateX: 0,
      rotateY: 0,
      duration: 0.6,
      ease: 'power3.out',
      overwrite: 'auto',
    });
  }, []);

  const handleMouseEnter = useCallback(() => {
    setIsHovered(true);
  }, []);

  return (
    <div
      ref={cardRef}
      className="card-3d reveal-item"
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      onMouseEnter={handleMouseEnter}
    >
      <div ref={innerRef} className="card-3d-inner">
        <div
          className={`bg-surface-1 border border-white/[0.06] rounded-xl overflow-hidden transition-all duration-300 ${
            isHovered ? `${module.glowClass} animated-border` : ''
          }`}
        >
          {/* Top color border accent */}
          <div
            className="h-[2px] w-full"
            style={{ backgroundColor: module.color }}
          />

          {/* Card content */}
          <div className="p-8">
            {/* Icon */}
            <div
              className="w-14 h-14 rounded-xl flex items-center justify-center"
              style={{ backgroundColor: `${module.color}1A` }}
            >
              <Icon size={28} strokeWidth={1.5} style={{ color: module.color }} />
            </div>

            {/* Module name & tagline */}
            <h3 className="font-space text-xl font-bold text-text-1 mt-5 mb-2">
              {module.name}
            </h3>
            <p className="text-sm text-text-2 mb-6">{module.tagline}</p>

            {/* Feature list */}
            <ul className="flex flex-col gap-3">
              {module.features.map((feature) => (
                <li key={feature} className="flex items-center gap-3">
                  <span
                    className="w-1.5 h-1.5 rounded-full flex-shrink-0"
                    style={{ backgroundColor: module.color }}
                  />
                  <span className="text-sm text-text-2">{feature}</span>
                </li>
              ))}
            </ul>

            {/* Explore link */}
            <div className="mt-6 pt-4 border-t border-white/[0.06]">
              <button
                className="group/link flex items-center gap-2 text-sm font-semibold transition-all duration-300 hover:gap-3"
                style={{ color: module.color }}
              >
                Explore
                <ArrowRight
                  size={14}
                  className="transition-transform duration-300 group-hover/link:translate-x-0.5"
                />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════
   CoreModules — Three interactive enterprise module cards
   ═══════════════════════════════════════════════════════ */

export default function CoreModules() {
  const containerRef = useScrollReveal({ y: 50, duration: 0.9, stagger: 0.15 });

  return (
    <section id="modules" className="landing-section bg-bg">
      <div ref={containerRef} className="landing-container">
        {/* ── Section Header ── */}
        <div className="text-center mb-16">
          <p className="reveal-item font-mono text-[11px] font-semibold tracking-[0.10em] uppercase text-[#00C896] mb-4">
            Core Modules
          </p>
          <h2 className="reveal-item font-space text-[clamp(1.75rem,4vw,3rem)] font-bold text-text-1 mb-4">
            Intelligence Modules
          </h2>
          <p className="reveal-item text-text-2 max-w-2xl mx-auto">
            Three purpose-built AI modules working in concert to protect lives,
            enforce compliance, and monitor infrastructure across India&apos;s
            road network.
          </p>
        </div>

        {/* ── Module Cards Grid ── */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {MODULES.map((mod) => (
            <ModuleCard key={mod.name} module={mod} />
          ))}
        </div>
      </div>
    </section>
  );
}