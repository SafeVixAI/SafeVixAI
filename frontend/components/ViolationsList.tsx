// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
import React from 'react';

'use client';

// A simple scrollable list to browse standard challans
const OFFENSES = [
  { section: '177', amount: '₹100 (₹300 repeat)', desc: 'General Provision (Not obeying basic rules)' },
  { section: '177A', amount: '₹500 (₹1500 repeat)', desc: 'Violation of road regulations (e.g. wrong way)' },
  { section: '181', amount: '₹5,000', desc: 'Driving without an active license' },
  { section: '183', amount: '₹1,000 - ₹2,000', desc: 'Over-speeding (based on vehicle type)' },
  { section: '184', amount: '₹1,000 - ₹5,000', desc: 'Dangerous driving / using phone while driving' },
  { section: '185', amount: '₹10,000 (₹15000 repeat)', desc: 'Drunken driving (above 30mg limit)' },
  { section: '194B', amount: '₹1,000', desc: 'Driving without a seat belt' },
  { section: '194D', amount: '₹1,000 + 3mo ban', desc: 'Driving without a helmet' },
];

export function ViolationsList() {
  return (
    <div className="card-glass" style={{ padding: '1.25rem' }}>
      <h3 style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-1)', marginBottom: '1rem' }}>
        Common Violations Directory
      </h3>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
        {OFFENSES.map((o) => (
          <div 
            key={o.section} 
            style={{ 
              display: 'flex', 
              flexDirection: 'column',
              padding: '0.75rem',
              background: 'var(--surface-2)',
              border: '1px solid var(--border)',
              borderRadius: '8px',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <span style={{ fontSize: '0.875rem', fontWeight: 700, color: 'var(--text-1)' }}>
                {o.desc}
              </span>
              <span style={{ fontSize: '0.875rem', fontWeight: 700, color: 'var(--warning)', whiteSpace: 'nowrap', marginLeft: '8px' }}>
                {o.amount}
              </span>
            </div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-2)', marginTop: '4px' }}>
              Section {o.section} of MV Act 1988
            </div>
          </div>
        ))}
      </div>
      <div style={{ textAlign: 'center', marginTop: '1rem', fontSize: '0.75rem', color: 'var(--text-3)' }}>
        Source: Motor Vehicles (Amendment) Act 2019
      </div>
    </div>
  );
}
