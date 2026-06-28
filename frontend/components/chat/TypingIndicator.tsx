// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

'use client';

import { useRef } from 'react';
import { gsap } from '@/lib/gsap';
import { useGSAP } from '@gsap/react';

export default function TypingIndicator() {
  const dot1Ref = useRef<HTMLSpanElement>(null);
  const dot2Ref = useRef<HTMLSpanElement>(null);
  const dot3Ref = useRef<HTMLSpanElement>(null);

  useGSAP(() => {
    const dots = [dot1Ref.current, dot2Ref.current, dot3Ref.current].filter(Boolean);
    /* istanbul ignore next */
    if (dots.length === 0) return;

    /* istanbul ignore next */
    gsap.fromTo(
      dots,
      { y: 0, opacity: 0.3 },
      {
        y: -6,
        opacity: 1,
        duration: 0.6,
        stagger: 0.15,
        repeat: -1,
        yoyo: true,
        ease: 'power2.inOut',
      }
    );
  }, []);

  return (
    <div className="flex gap-2 items-center px-4 py-3.5 rounded-tr-2xl rounded-tl-2xl rounded-br-2xl rounded-bl-sm mr-12 bg-[--surface-2] border border-[--border] shadow-md shadow-black/10 backdrop-blur-xl w-fit">
      <span ref={dot1Ref} className="w-2 h-2 bg-brand rounded-full inline-block" />
      <span ref={dot2Ref} className="w-2 h-2 bg-brand rounded-full inline-block" />
      <span ref={dot3Ref} className="w-2 h-2 bg-brand rounded-full inline-block" />
    </div>
  );
}
