'use client';

// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team


import React from 'react';
import Link from 'next/link';
import { MapPin, Phone, Users, Navigation, Building2 } from 'lucide-react';
import type { Municipality } from '@/lib/api';

const STATE_COLORS: Record<string, string> = {
  MH: 'bg-orange-500/20 text-orange-400',
  TN: 'bg-emerald-500/20 text-emerald-400',
  AP: 'bg-sky-500/20 text-sky-400',
  KA: 'bg-red-500/20 text-red-400',
  TS: 'bg-pink-500/20 text-pink-400',
  DL: 'bg-amber-500/20 text-amber-400',
  WB: 'bg-lime-500/20 text-lime-400',
  UP: 'bg-violet-500/20 text-violet-400',
  GJ: 'bg-teal-500/20 text-teal-400',
  RJ: 'bg-rose-500/20 text-rose-400',
  MP: 'bg-cyan-500/20 text-cyan-400',
  KL: 'bg-green-500/20 text-green-400',
  BR: 'bg-yellow-500/20 text-yellow-400',
  PB: 'bg-indigo-500/20 text-indigo-400',
};

function formatPopulation(pop: number | null): string {
  if (!pop) return '—';
  if (pop >= 10_000_000) return `${(pop / 10_000_000).toFixed(1)} Cr`;
  if (pop >= 100_000) return `${(pop / 100_000).toFixed(1)} L`;
  if (pop >= 1_000) return `${(pop / 1_000).toFixed(0)}K`;
  return String(pop);
}

interface MunicipalityCardProps {
  municipality: Municipality;
}

export function MunicipalityCard({ municipality: m }: MunicipalityCardProps) {
  const stateColor = STATE_COLORS[m.stateCode] ?? 'bg-brand/20 text-brand-light';

  return (
    <Link
      href={`/guide/${m.slug}`}
      className="group relative flex flex-col p-5 rounded-2xl bg-surface-2/70 border border-border hover:border-brand/40 hover:bg-surface-2 transition-all duration-300 overflow-hidden"
    >
      {/* Gradient overlay on hover */}
      <div className="absolute inset-0 bg-gradient-to-br from-brand/[0.04] to-transparent opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none" />

      {/* Header */}
      <div className="flex items-start justify-between gap-3 mb-3 relative">
        <div className="flex-1 min-w-0">
          <h3 className="text-sm font-bold text-text-1 group-hover:text-brand-light transition-colors truncate">
            {m.name}
          </h3>
          <div className="flex items-center gap-1.5 mt-1.5 text-text-3">
            <MapPin size={12} className="shrink-0" />
            <span className="text-xs truncate">{m.city}, {m.stateCode}</span>
          </div>
        </div>
        <span className={`shrink-0 px-2 py-0.5 rounded-md text-[10px] font-bold uppercase tracking-wider ${stateColor}`}>
          {m.stateCode}
        </span>
      </div>

      {/* Stats row */}
      <div className="flex items-center gap-3 mt-auto relative">
        {m.population && (
          <div className="flex items-center gap-1 text-text-3">
            <Users size={11} />
            <span className="text-[11px] font-semibold font-mono">{formatPopulation(m.population)}</span>
          </div>
        )}
        {m.wardCount && (
          <div className="flex items-center gap-1 text-text-3">
            <Building2 size={11} />
            <span className="text-[11px] font-semibold font-mono">{m.wardCount} wards</span>
          </div>
        )}
        {m.distanceKm != null && (
          <div className="flex items-center gap-1 text-brand-light">
            <Navigation size={11} />
            <span className="text-[11px] font-semibold font-mono">{m.distanceKm.toFixed(1)} km</span>
          </div>
        )}
      </div>

      {/* Helpline badge */}
      {m.helplinePhone && (
        <div className="mt-3 flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20 w-fit">
          <Phone size={11} className="text-emerald-400" />
          <span className="text-[11px] font-bold text-emerald-400 font-mono">{m.helplinePhone}</span>
        </div>
      )}

      {/* Type badge */}
      <div className="absolute top-0 right-0 px-3 py-1 rounded-bl-xl bg-surface-3/80 text-[9px] font-bold uppercase tracking-widest text-text-3">
        {m.municipalityType === 'municipal_corporation' ? 'Corp' : 'Muni'}
      </div>
    </Link>
  );
}