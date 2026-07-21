'use client';

// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
import React from 'react';


export function AuthorityCard() {
 return (
 <div 
 className="card-glass" 
 style={{
 padding: '1rem',
 marginTop: '1rem',
 background: 'rgba(255, 255, 255, 0.03)',
 border: '1px solid rgba(255, 255, 255, 0.1)',
 display: 'flex',
 alignItems: 'center',
 gap: '1rem'
 }}
 >
  <div style={{ width: '40px', height: '40px', borderRadius: '50%', background: 'var(--surface-container-high)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1.2rem' }}>
  🏛️
  </div>
 <div>
 <div style={{ fontSize: '0.75rem', textTransform: 'uppercase', color: 'var(--text-secondary)', letterSpacing: '0.05em', fontWeight: 600 }}>
 Assigned Authority
 </div>
 <div style={{ fontSize: '1rem', color: 'var(--text-primary)', fontWeight: 700 }}>
 NHAI (Zone 4)
 </div>
 <div style={{ fontSize: '0.875rem', color: 'var(--accent-green)', marginTop: '2px' }}>
 Response SLA: 24h
 </div>
 </div>
 </div>
 );
}