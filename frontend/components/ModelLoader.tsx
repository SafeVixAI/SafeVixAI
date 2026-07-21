'use client';

// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
import React from 'react';


import { useAppStore } from '@/lib/store';
import { useShallow } from 'zustand/react/shallow';

export function ModelLoader() {
  const { aiMode, modelLoadProgress } = useAppStore(useShallow((s) => ({ aiMode: s.aiMode, modelLoadProgress: s.modelLoadProgress })));

  if (aiMode !== 'loading') return null;

  return (
    <div 
      className="animate-fade-in-up"
      style={{
        position: 'absolute',
        top: 0, left: 0, right: 0, bottom: 0,
        background: 'rgba(7, 19, 37, 0.85)',
        backdropFilter: 'blur(10px)',
        zIndex: 50,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '2rem',
        textAlign: 'center'
      }}
    >
      <div style={{
        width: '64px',
        height: '64px',
        borderRadius: '50%',
        background: 'var(--surface-2)',
        border: '3px solid var(--brand-light)',
        borderTopColor: 'transparent',
        animation: 'spin 1s linear infinite',
        marginBottom: '1.5rem',
      }} />
      
      <div style={{ fontSize: '1.25rem', fontWeight: 600, color: '#fff', marginBottom: '0.5rem' }}>
        Loading Offline AI Model
      </div>
      <div style={{ fontSize: '0.875rem', color: 'var(--text-2)', marginBottom: '1.5rem', maxWidth: '300px' }}>
        Loading the local Gemma safety model for on-device inference. Low-memory devices automatically stay on the online safety router.
      </div>

      <div style={{ width: '100%', maxWidth: '300px', height: '6px', background: 'var(--surface-1)', borderRadius: '99px', overflow: 'hidden' }}>
        <div 
          style={{ 
            height: '100%', 
            width: `${modelLoadProgress}%`,
            background: 'var(--brand-light)',
            transition: 'width 0.3s ease'
          }} 
        />
      </div>
      <div style={{ marginTop: '0.5rem', fontSize: '0.75rem', color: 'rgba(255,255,255,0.8)', fontWeight: 600 }}>
        {Math.round(modelLoadProgress)}%
      </div>
    </div>
  );
}