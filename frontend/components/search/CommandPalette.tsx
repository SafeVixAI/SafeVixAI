'use client';

// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
import React from 'react';

// frontend/components/search/CommandPalette.tsx
// Cmd+K search overlay using cmdk

import { Command } from 'cmdk';
import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { useGSAP } from '@gsap/react';
import { gsap } from '@/lib/gsap';

export function CommandPalette() {
  const [open, setOpen] = useState(false);
  const overlayRef = useRef<HTMLDivElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);
  const router = useRouter();

  // Cmd+K or Ctrl+K to open
  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (e.key === 'k' && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        setOpen((o) => !o);
      }
    };
    document.addEventListener('keydown', down);
    return () => document.removeEventListener('keydown', down);
  }, []);

  // GSAP animate in/out — useGSAP for proper React 19 cleanup
  useGSAP(() => {
    if (!overlayRef.current || !panelRef.current) return;
    if (open) {
      gsap.fromTo(
        overlayRef.current,
        { opacity: 0 },
        { opacity: 1, duration: 0.15 }
      );
      gsap.fromTo(
        panelRef.current,
        { opacity: 0, scale: 0.96, y: -8 },
        { opacity: 1, scale: 1, y: 0, duration: 0.2, ease: 'power2.out' }
      );
    }
  }, { dependencies: [open] });

  const navigate = (path: string) => {
    setOpen(false);
    router.push(path);
  };

  if (!open) return null;

  return (
    <div
      ref={overlayRef}
      role="dialog"
      aria-modal="true"
      aria-label="Search commands"
      className="fixed inset-0 z-[100] bg-black/50 backdrop-blur-sm"
      onClick={() => setOpen(false)}
    >
      <div
        ref={panelRef}
        className="absolute top-[20%] left-1/2 -translate-x-1/2 w-[calc(100%-32px)] max-w-lg bg-surface-4 border border-border-md rounded-xl shadow-modal"
        onClick={(e) => e.stopPropagation()}
      >
        <Command>
          <Command.Input
            placeholder="Search hospitals, first aid, emergency..."
            autoFocus
            className="w-full bg-transparent px-4 py-3 text-text-1 border-b border-border outline-none text-body font-sans"
          />
          <Command.List className="max-h-[288px] overflow-y-auto p-2">
            <Command.Empty className="px-4 py-6 text-center text-text-3 text-body-sm">
              No results found
            </Command.Empty>

            <Command.Group
              heading="Emergency"
              className="[&_[cmdk-group-heading]]:text-micro [&_[cmdk-group-heading]]:font-semibold [&_[cmdk-group-heading]]:tracking-[0.1em] [&_[cmdk-group-heading]]:uppercase [&_[cmdk-group-heading]]:text-text-3 [&_[cmdk-group-heading]]:px-2 [&_[cmdk-group-heading]]:pt-2 [&_[cmdk-group-heading]]:pb-1"
            >
              <CommandItem onSelect={() => navigate('/locator')}>
                Find nearest hospital
              </CommandItem>
              <CommandItem onSelect={() => navigate('/emergency')}>
                Activate Emergency SOS
              </CommandItem>
            </Command.Group>

            <Command.Group
              heading="Features"
              className="[&_[cmdk-group-heading]]:text-micro [&_[cmdk-group-heading]]:font-semibold [&_[cmdk-group-heading]]:tracking-[0.1em] [&_[cmdk-group-heading]]:uppercase [&_[cmdk-group-heading]]:text-text-3 [&_[cmdk-group-heading]]:px-2 [&_[cmdk-group-heading]]:pt-2 [&_[cmdk-group-heading]]:pb-1"
            >
              <CommandItem onSelect={() => navigate('/first-aid')}>
                First Aid Guide
              </CommandItem>
              <CommandItem onSelect={() => navigate('/challan')}>
                Calculate Traffic Fine
              </CommandItem>
              <CommandItem onSelect={() => navigate('/report')}>
                Report Road Issue
              </CommandItem>
              <CommandItem onSelect={() => navigate('/assistant')}>
                AI Assistant
              </CommandItem>
            </Command.Group>
          </Command.List>
        </Command>
      </div>
    </div>
  );
}

function CommandItem({
  children,
  onSelect,
}: {
  children: React.ReactNode;
  onSelect: () => void;
}) {
  return (
    <Command.Item
      onSelect={onSelect}
      className="command-item px-3 py-2 rounded-md cursor-pointer text-body text-text-1 flex items-center gap-2 transition-colors data-[selected]:bg-surface-3 aria-selected:bg-surface-3"
    >
      {children}
    </Command.Item>
  );
}