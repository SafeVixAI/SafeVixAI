// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
import React from 'react';

'use client';

import { useState, useEffect, useRef } from 'react';
import { useGSAP } from '@gsap/react';
import { gsap } from '@/lib/gsap';

const SHORTCUTS = [
  { keys: 'Cmd+K', action: 'Open command palette' },
  { keys: '?', action: 'Toggle keyboard shortcuts' },
  { keys: 'Arrow keys', action: 'Pan map' },
  { keys: '+ / -', action: 'Zoom map in/out' },
  { keys: 'Esc', action: 'Close dialogs / Cancel SOS' },
  { keys: 'Enter', action: 'Send chat message / Confirm action' },
];

export function KeyboardShortcutsHelp() {
  const [open, setOpen] = useState(false);
  const overlayRef = useRef<HTMLDivElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === '?' && !e.metaKey && !e.ctrlKey && !e.altKey) {
        const tag = (e.target as HTMLElement)?.tagName;
        if (tag === 'INPUT' || tag === 'TEXTAREA') return;
        e.preventDefault();
        setOpen((o) => !o);
      }
      if (e.key === 'Escape' && open) setOpen(false);
    };
    document.addEventListener('keydown', handler);
    return () => document.removeEventListener('keydown', handler);
  }, [open]);

  useGSAP(() => {
    if (!overlayRef.current || !panelRef.current) return;
    if (open) {
      gsap.fromTo(overlayRef.current, { opacity: 0 }, { opacity: 1, duration: 0.12 });
      gsap.fromTo(panelRef.current, { opacity: 0, y: -6 }, { opacity: 1, y: 0, duration: 0.18, ease: 'power2.out' });
    }
  }, { dependencies: [open] });

  if (!open) return null;

  return (
    <div
      ref={overlayRef}
      role="dialog"
      aria-modal="true"
      aria-label="Keyboard shortcuts"
      className="fixed inset-0 z-[110] bg-black/40 backdrop-blur-sm flex items-center justify-center"
      onClick={() => setOpen(false)}
    >
      <div
        ref={panelRef}
        className="w-[calc(100%-32px)] max-w-md bg-surface-4 border border-border-md rounded-xl shadow-modal p-5"
        onClick={(e) => e.stopPropagation()}
      >
        <h2 className="text-micro font-semibold uppercase tracking-[0.14em] text-text-3 mb-4">
          Keyboard Shortcuts
        </h2>
        <div className="space-y-2.5">
          {SHORTCUTS.map((s) => (
            <div key={s.keys} className="flex items-center justify-between">
              <span className="text-body-sm text-text-1">{s.action}</span>
              <kbd className="px-2 py-0.5 bg-surface-2 border border-border-md rounded text-micro font-mono text-text-2">
                {s.keys}
              </kbd>
            </div>
          ))}
        </div>
        <p className="mt-4 text-micro text-text-3 text-center">Press ? or Esc to close</p>
      </div>
    </div>
  );
}
