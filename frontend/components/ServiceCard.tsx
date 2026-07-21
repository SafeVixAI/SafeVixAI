'use client';

// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
import React from 'react';


import { useState, memo, useCallback, useMemo } from 'react';
import { NearbyService } from '@/lib/store';
import {
 openBestNavApp,
 openNavApp,
 getPreferredNavApp,
 setPreferredNavApp,
 NAV_APPS,
 type NavApp,
} from '@/lib/navigation-launch';

// ── Accent colors per category ────────────────────────────────────────────────

const ACCENT_COLORS: Record<NearbyService['category'], string> = {
 hospital: 'var(--emergency)',
 ambulance: 'var(--emergency)',
 police: '#3B82F6',
 fire: 'var(--warning)',
 towing: 'var(--warning)',
 pharmacy: '#818CF8',
 puncture: 'var(--brand-light)',
 showroom: '#3B82F6',
};

const CATEGORY_LABELS: Record<NearbyService['category'], string> = {
 hospital: 'Hospital',
 ambulance: 'Ambulance',
 police: 'Police Station',
 fire: 'Fire Station',
 towing: 'Towing Service',
 pharmacy: 'Pharmacy',
 puncture: 'Puncture Shop',
 showroom: 'Showroom',
};

interface Props {
 service: NearbyService;
 className?: string;
}

function formatDistance(metres: number): string {
 return metres < 1000
 ? `${metres.toFixed(0)} m`
 : `${(metres / 1000).toFixed(1)} km`;
}

export const ServiceCard = memo(function ServiceCard({ service, className = '' }: Props) {
 const color = ACCENT_COLORS[service.category];
 const label = CATEGORY_LABELS[service.category];
 const [showNavChoice, setShowNavChoice] = useState(false);

 const dest = useMemo(() => ({ lat: service.lat, lon: service.lon, name: service.name }), [service.lat, service.lon, service.name]);

 const handleNavSelect = useCallback((app: NavApp) => {
 setPreferredNavApp(app);
 openNavApp(app, dest);
 setShowNavChoice(false);
 }, [dest]);

 return (
 <div className={`service-card ${className}`} role="article" aria-label={service.name}>
 {/* Left accent bar */}
  <div className="sv-service-accent" style={{ backgroundColor: color }} aria-hidden="true" />

  <div className="sv-service-body">
  {/* Top row: name + distance */}
  <div className="sv-service-top">
  <div>
  <div className="sv-service-name">{service.name}</div>
 <div style={{ color, fontSize: '0.75rem', fontWeight: 600, marginTop: '2px' }}>
 {label}
 {service.source === 'offline' && (
 <span style={{
 marginLeft: '0.5rem',
 color: 'var(--text-3)',
 fontWeight: 400,
 }}>
 · offline cache
 </span>
 )}
 </div>
 </div>
  <div className="sv-service-dist">{formatDistance(service.distance)}</div>
 </div>

  {/* Actions row */}
  <div className="sv-service-actions">
 {service.phone && (
 <a
 href={`tel:${service.phone}`}
  className="inline-flex items-center justify-center gap-2 px-3 py-1.5 rounded-lg text-xs font-bold border border-brand-light/30 text-brand-light hover:bg-brand-light/10 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-light/40"
 aria-label={`Call ${service.name}: ${service.phone}`}
 >
 Call
 </a>
 )}

  {/* Primary: open in preferred nav app */}
  <button
  onClick={() => openBestNavApp(dest)}
  className="inline-flex items-center justify-center gap-2 px-3 py-1.5 rounded-lg text-xs font-bold border border-brand/30 text-brand hover:bg-brand/10 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand/40"
  aria-label={`Get directions to ${service.name}`}
  >
   Map Directions
  </button>

  {/* Secondary: nav app chooser dropdown */}
  <div className="relative">
  <button
  onClick={() => setShowNavChoice(!showNavChoice)}
  className="inline-flex items-center justify-center gap-2 px-3 py-1.5 rounded-lg text-xs font-bold border border-brand/30 text-brand hover:bg-brand/10 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand/40"
  aria-label="Choose navigation app"
 style={{ padding: '0.25rem 0.5rem', minWidth: 'auto' }}
 title={`Using: ${NAV_APPS.find(a => a.key === getPreferredNavApp())?.label || 'Google Maps'}`}
 >
 ⌄
 </button>

 {/* Dropdown */}
 {showNavChoice && (
 <div
 className="absolute right-0 bottom-full mb-2 z-50 min-w-[160px] rounded-lg overflow-hidden shadow-2xl border"
 style={{
 backgroundColor: 'var(--surface-1)',
 borderColor: 'var(--border)',
 }}
 >
 {NAV_APPS.map((app) => {
 const isActive = getPreferredNavApp() === app.key;
 return (
 <button
 key={app.key}
 onClick={() => handleNavSelect(app.key)}
 className="w-full flex items-center gap-3 px-4 py-3 text-left text-xs font-bold uppercase tracking-wider transition-colors"
 style={{
 color: isActive ? 'var(--brand)' : 'var(--text-1)',
 backgroundColor: isActive ? 'var(--brand-dim)' : 'transparent',
 }}
 >
 <span className="text-base">{app.emoji}</span>
 {app.label}
 {isActive && <span className="ml-auto text-[10px] opacity-60"></span>}
 </button>
 );
 })}
 </div>
 )}
 </div>
 </div>
 </div>
 </div>
 );
});
