'use client';

// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
import React from 'react';


import { useRef } from 'react';
import { HelpCircle } from 'lucide-react';
import { gsap } from '@/lib/gsap';
import { useGSAP } from '@gsap/react';

const SUGGESTED_STARTERS = [
  " Help! I've been in an accident, what do I do?",
  " Send an ambulance to my current location",
  "Explain the hit-and-run legal procedure",
  "What are my rights during a police inspection?"
];

interface SuggestedInquiriesProps {
  onSelect: (_text: string) => void;
}

export default function SuggestedInquiries({ onSelect }: SuggestedInquiriesProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  useGSAP(() => {
    /* istanbul ignore next */
    if (!containerRef.current) return;
/* istanbul ignore next */
    const chips = containerRef.current.querySelectorAll('.suggested-chip');

    /* istanbul ignore next */
    gsap.fromTo(
      chips,
      { opacity: 0, y: 15, scale: 0.95 },
      {
        opacity: 1,
        y: 0,
        scale: 1,
        duration: 0.5,
        stagger: 0.08,
        ease: 'power3.out',
        clearProps: 'all',
      }
    );
  }, { scope: containerRef });

  return (
    <div ref={containerRef} className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 w-full mt-2">
      {SUGGESTED_STARTERS.map((text, i) => (
        <button
          key={i}
          onClick={() => onSelect(text)}
          className="suggested-chip group bg-[--surface-2] hover:bg-[--surface-3] backdrop-blur-md transition-all duration-200 px-4 py-3.5 rounded-xl text-left border border-[--border] hover:border-brand/30 hover:shadow-md flex items-start gap-3 opacity-0"
        >
          <div className="mt-0.5 p-1.5 rounded-lg bg-brand/10 text-brand group-hover:scale-110 transition-transform flex-shrink-0">
            <HelpCircle size={14} />
          </div>
          <span className="text-[13px] text-text-1 font-semibold leading-snug">{text}</span>
        </button>
      ))}
    </div>
  );
}