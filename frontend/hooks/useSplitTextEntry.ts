// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

'use client';

import { useRef } from 'react';
import { useGSAP } from '@gsap/react';
import { gsap } from '@/lib/gsap';

interface SplitTextInstance {
  chars: Element[];
}

type SplitTextClass = new (target: any, vars?: any) => SplitTextInstance;

let SplitText: SplitTextClass | null = null;

async function loadSplitText() {
  /* istanbul ignore next */
  if (typeof window === 'undefined') return;
  try {
    const mod = await import('gsap/SplitText');
    SplitText = mod.SplitText;
    gsap.registerPlugin(mod.SplitText);
  } catch {
    // commercial plugin is unavailable; standard DOM fallback is leveraged
  }
}

if (typeof window !== 'undefined') {
  loadSplitText();
}

export function useSplitTextEntry() {
  const headingRef = useRef<HTMLHeadingElement>(null);

  useGSAP(
    () => {
      if (!headingRef.current) return;

      const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
      /* istanbul ignore next */
      if (prefersReducedMotion) return;

      const originalHTML = headingRef.current.innerHTML;

      if (SplitText) {
        const split = new SplitText(headingRef.current, {
          type: 'chars',
          charsClass: 'split-char',
        });

        gsap.fromTo(
          split.chars,
          { opacity: 0, y: 12, willChange: 'transform, opacity' },
          {
            opacity: 1,
            y: 0,
            duration: 0.4,
            stagger: 0.025,
            ease: 'power2.out',
            clearProps: 'willChange',
            onComplete: () => {
              if (headingRef.current) {
                headingRef.current.innerHTML = originalHTML;
              }
            },
          }
        );
      } else {
        // High-performance pure DOM/CSS fallback — safe DOM manipulation (no innerHTML from unsanitized input)
        const text = headingRef.current.textContent || '';
        const fragment = document.createDocumentFragment();
        for (const char of text) {
          const span = document.createElement('span');
          span.className = 'split-char inline-block';
          span.style.opacity = '0';
          span.style.willChange = 'transform, opacity';
          span.textContent = char === ' ' ? '\u00A0' : char;
          fragment.appendChild(span);
        }
        headingRef.current.textContent = '';
        headingRef.current.appendChild(fragment);

        const chars = headingRef.current.querySelectorAll('.split-char');
        gsap.fromTo(
          chars,
          { opacity: 0, y: 12 },
          {
            opacity: 1,
            y: 0,
            duration: 0.4,
            stagger: 0.025,
            ease: 'power2.out',
            clearProps: 'all',
            onComplete: () => {
              /* istanbul ignore next */
              if (headingRef.current) {
                headingRef.current.innerHTML = originalHTML;
              }
            },
          }
        );
      }
    },
    { scope: headingRef }
  );

  return headingRef;
}
