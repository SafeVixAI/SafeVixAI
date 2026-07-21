'use client';

// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
import React from 'react';


import { ReactNode, memo } from 'react';

interface FirstAidCardProps {
  title: string;
  icon: string | ReactNode;
  steps: string[];
}

/** Converts **bold** markers to React <strong> elements without injecting raw HTML. */
function renderStep(step: string): ReactNode {
  const parts = step.split(/\*\*(.*?)\*\*/g);
  return parts.map((part, i) =>
    i % 2 === 1 ? (
      <strong key={i} style={{ color: 'var(--text-primary)' }}>{part}</strong>
    ) : (
      <span key={i}>{part}</span>
    )
  );
}

export const FirstAidCard = memo(function FirstAidCard({ title, icon, steps }: FirstAidCardProps) {
  return (
    <div
      className="card-glass"
      style={{
        position: 'relative',
        padding: '1.5rem',
        background: 'var(--surface-container-low)',
        border: 'none',
        boxShadow: '0 8px 32px rgba(3, 14, 32, 0.4), inset 0 1px 1px rgba(255, 255, 255, 0.05)',
        borderRadius: 'var(--card-radius)',
        display: 'flex',
        flexDirection: 'column',
        gap: '1rem',
        overflow: 'hidden',
      }}
    >
      {/* Accent Glow */}
      <div
        style={{
          position: 'absolute',
          top: '-20px',
          left: '-20px',
          width: '100px',
          height: '100px',
          background: 'radial-gradient(circle, var(--accent-red) 0%, transparent 70%)',
          opacity: 0.15,
          pointerEvents: 'none',
        }}
      />

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div
            style={{
              fontSize: '2rem',
              padding: '0.5rem',
              background: 'var(--surface-container-lowest)',
              borderRadius: '12px',
            }}
          >
            {icon}
          </div>
          <h3 style={{ fontSize: '1.125rem', fontWeight: 700, color: 'var(--text-primary)' }}>
            {title}
          </h3>
        </div>

        {/* Offline Badge */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '4px',
            padding: '4px 8px',
            background: 'var(--surface-container-highest)',
            borderRadius: '12px',
            border: '1px solid rgba(83, 225, 111, 0.2)',
          }}
        >
          <span className="conn-dot" style={{ background: 'var(--accent-green)', width: '6px', height: '6px' }} />
          <span
            style={{
              fontSize: '0.625rem',
              fontWeight: 600,
              color: 'var(--accent-green)',
              letterSpacing: '0.05em',
              textTransform: 'uppercase',
            }}
          >
            Offline
          </span>
        </div>
      </div>

      <div style={{ marginTop: '0.5rem' }}>
        <ol
          style={{
            margin: 0,
            paddingLeft: '1.25rem',
            color: 'var(--text-secondary)',
            fontSize: '0.875rem',
            lineHeight: 1.6,
            display: 'flex',
            flexDirection: 'column',
            gap: '0.5rem',
          }}
        >
          {steps.map((step, idx) => (
            <li key={idx} style={{ paddingLeft: '0.5rem' }}>
              {renderStep(step)}
            </li>
          ))}
        </ol>
      </div>
    </div>
  );
});