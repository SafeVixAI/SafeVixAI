'use client';

// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team


import React from 'react';
import { User, Phone } from 'lucide-react';
import type { MunicipalityDetail } from '@/lib/api';

interface LeadershipCardProps {
  municipality: MunicipalityDetail;
}

function LeaderFigure({
  title,
  name,
  phone,
  initials,
}: {
  title: string;
  name: string | null;
  phone?: string | null;
  initials: string;
}) {
  return (
    <div className="flex items-center gap-4 p-4 rounded-xl bg-surface-2/50 border border-border">
      {/* Avatar */}
      <div className="w-14 h-14 rounded-full bg-gradient-to-br from-brand/30 to-brand-light/20 border-2 border-brand/30 flex items-center justify-center shrink-0">
        {name ? (
          <span className="text-lg font-bold text-brand-light">{initials}</span>
        ) : (
          <User size={24} className="text-text-3" />
        )}
      </div>

      <div className="flex-1 min-w-0">
        <p className="text-[10px] font-semibold uppercase tracking-widest text-text-3 mb-1">{title}</p>
        <p className={`text-sm font-bold truncate ${name ? 'text-text-1' : 'text-text-3 italic'}`}>
          {name ?? 'Information not available'}
        </p>
        {phone && (
          <a
            href={`tel:${phone}`}
            className="flex items-center gap-1.5 mt-1 text-brand-light hover:text-brand transition-colors"
          >
            <Phone size={11} />
            <span className="text-xs font-mono">{phone}</span>
          </a>
        )}
      </div>
    </div>
  );
}

function getInitials(name: string | null): string {
  if (!name) return '?';
  return name
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map((w) => w[0])
    .join('')
    .toUpperCase();
}

export function LeadershipCard({ municipality: m }: LeadershipCardProps) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
      <LeaderFigure
        title="Mayor"
        name={m.mayorName}
        initials={getInitials(m.mayorName)}
      />
      <LeaderFigure
        title="Commissioner"
        name={m.commissionerName}
        phone={m.commissionerPhone}
        initials={getInitials(m.commissionerName)}
      />
    </div>
  );
}