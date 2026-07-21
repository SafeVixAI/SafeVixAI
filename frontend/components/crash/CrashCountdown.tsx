'use client';

// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
import React from 'react';


import { useState, useEffect, useRef } from 'react';
import { useGSAP } from '@gsap/react';
import { useAppStore } from '@/lib/store';
import { gsap } from '@/lib/gsap';
import { ProgressRing } from './ProgressRing';
import { haptics } from '@/lib/haptics';
import { sounds } from '@/lib/sounds';

interface CrashCountdownProps {
  severity: string;
  onCancel: () => void;
  onDispatch: () => void;
}

export function CrashCountdown({ severity, onCancel, onDispatch }: CrashCountdownProps) {
  const [seconds, setSeconds] = useState(20);
  const userProfile = useAppStore((state) => state.userProfile);
  const soundsEnabled = useAppStore((state) => state.soundsEnabled);
  const dispatched = useRef(false);
  const numRef = useRef<HTMLParagraphElement>(null);
  const bgRef = useRef<HTMLDivElement>(null);
  const cancelBtnRef = useRef<HTMLButtonElement>(null);

  // Initial haptic + entry animation
  useGSAP(() => {
    haptics.sos();

    if (cancelBtnRef.current) {
      gsap.fromTo(cancelBtnRef.current,
        { opacity: 0, y: 20 },
        { opacity: 1, y: 0, duration: 0.4, delay: 0.3, ease: 'power2.out' }
      );
    }
  }, { scope: bgRef });

  // Countdown timer
  useEffect(() => {
    const t = window.setInterval(() => {
      setSeconds((s) => {
        if (s <= 1 && !dispatched.current) {
          dispatched.current = true;
          onDispatch();
          clearInterval(t);
        }
        return s - 1;
      });
    }, 1000);
    return () => clearInterval(t);
  }, [onDispatch]);

  // GSAP animations per second tick
  useGSAP(() => {
    if (!numRef.current) return;

    // Number flips down - like a mechanical counter
    gsap.fromTo(numRef.current,
      { opacity: 0, y: -20, scale: 1.1 },
      { opacity: 1, y: 0, scale: 1, duration: 0.2, ease: 'power3.out' }
    );

    // Background gets more red/intense as count drops
    if (bgRef.current && seconds <= 10) {
      gsap.to(bgRef.current, {
        background: 'linear-gradient(135deg, #2D0808 0%, #4A0A0A 100%)',
        duration: 0.5
      });
    }

    // Flash effect for last 5 seconds
    if (bgRef.current && seconds <= 5) {
      gsap.to(bgRef.current, {
        opacity: 0.85, duration: 0.1,
        yoyo: true, repeat: 3
      });
      haptics.heavy();
    }

    // Sound tick
    if (soundsEnabled) {
      sounds.countdown(seconds);
    }
  }, { dependencies: [seconds, soundsEnabled], scope: bgRef });

  return (
    <div
      ref={bgRef}
      role="alertdialog"
      aria-live="assertive"
      aria-modal="true"
      className="fixed inset-0 z-[9999] bg-gradient-to-br from-[#1A0A0A] to-[#2D0808] flex flex-col items-center justify-center p-6"
    >
      {/* Severity badge */}
      <span className="sv-micro text-white/60 mb-2">
        {severity.toUpperCase()} CRASH DETECTED
      </span>

      {/* Countdown number - mechanical counter */}
      <p
        ref={numRef}
        aria-label={`${seconds} seconds to auto SOS`}
        className={`crash-countdown-num text-8xl font-extrabold leading-none m-0 tabular-nums font-mono transition-colors duration-300 ${
          seconds <= 5 ? 'text-red-600' : 'text-white'
        }`}
      >
        {seconds}
      </p>

      <p className="text-white/70 text-body my-3">
        Emergency services will be called in {seconds}s
      </p>

      {/* User info */}
      <div className="flex gap-4 mb-8">
        <span className="text-white/50 text-caption">
          {userProfile.bloodGroup || 'Blood group not set'}
        </span>
        <span className="text-white/50 text-caption">
          {userProfile.vehicleNumber || 'Vehicle not set'}
        </span>
      </div>

      {/* Cancel button - explicit language */}
      <button
        ref={cancelBtnRef}
        onClick={onCancel}
        autoFocus
        className="px-12 py-4 bg-white text-red-800 font-bold text-h2 rounded-lg border-none cursor-pointer min-w-[240px] min-h-[56px] hover:scale-105 active:scale-95 transition-transform"
      >
        I AM SAFE — CANCEL SOS
      </button>

      {/* Progress ring - GSAP animated */}
      <div className="absolute top-6 right-6">
        <ProgressRing seconds={seconds} total={20} size={64} />
      </div>
    </div>
  );
}