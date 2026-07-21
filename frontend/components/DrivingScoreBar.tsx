'use client';

// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team


import React from 'react';
import { useAppStore } from '@/lib/store';
import { useShallow } from 'zustand/react/shallow';

export function DrivingScoreBar() {
  const { drivingScore } = useAppStore(useShallow((s) => ({ drivingScore: s.drivingScore })));
  
  // Example max score 100
  const normalized = Math.max(0, Math.min(100, drivingScore || 0));
  let color = 'var(--accent-red)';
  if (normalized > 50) color = 'var(--accent-orange)';
  if (normalized > 80) color = 'var(--accent-green)';

  return (
    <div className="card-glass" style={{ padding: '1.25rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
        <span style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>Sentinel Driving Score</span>
        <span style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text-primary)' }}>{normalized}/100</span>
      </div>
      <div style={{ width: '100%', height: '8px', background: 'var(--surface-container-highest)', borderRadius: '4px', overflow: 'hidden' }}>
        <div 
          style={{
            height: '100%',
            width: `${normalized}%`,
            background: color,
            transition: 'width 1s ease-out, background 0.5s ease',
            boxShadow: `0 0 10px ${color}`
          }}
        />
      </div>
      <p style={{ marginTop: '0.75rem', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
        Based on device telemetry (acceleration, braking) — processed 100% on edge.
      </p>
    </div>
  );
}