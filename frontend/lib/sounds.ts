// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

// frontend/lib/sounds.ts - Web Audio API (no library needed)
// Subtle audio feedback for critical moments. Optional in Settings.

import { useAppStore } from './store';

let ctx: AudioContext | null = null;

function getAudioContext(): AudioContext | null {
  /* istanbul ignore next */
  if (typeof window === 'undefined') return null;
  if (!ctx) {
    try {
      ctx = new AudioContext();
    } catch {
      return null;
    }
  }
  return ctx;
}

function playTone(freq: number, duration: number, gain = 0.1) {
  /* istanbul ignore next */
  if (typeof window === 'undefined') return;
  // Guard with soundsEnabled setting from Zustand store
  if (!useAppStore.getState().soundsEnabled) return;

  const audioCtx = getAudioContext();
  if (!audioCtx) return;

  // Resume context if suspended (browser autoplay policy)
  if (audioCtx.state === 'suspended') {
    audioCtx.resume();
  }

  const osc = audioCtx.createOscillator();
  const gainNode = audioCtx.createGain();
  osc.connect(gainNode);
  gainNode.connect(audioCtx.destination);
  osc.frequency.value = freq;
  gainNode.gain.setValueAtTime(gain, audioCtx.currentTime);
  gainNode.gain.exponentialRampToValueAtTime(
    0.001,
    audioCtx.currentTime + duration
  );
  osc.start(audioCtx.currentTime);
  osc.stop(audioCtx.currentTime + duration);
}

export const sounds = {
  sosSent: () => playTone(880, 0.3, 0.15), // high alert
  reportSent: () => playTone(440, 0.2, 0.08), // confirmation
  countdown: (s: number) => playTone(s <= 5 ? 660 : 440, 0.1), // tick
  error: () => playTone(220, 0.4, 0.12), // low error
  sev5Alert: () => {
    playTone(987.77, 0.15, 0.15); // B5 note
    setTimeout(() => playTone(1318.51, 0.3, 0.15), 120); // E6 note (urgent alarm)
  },
};
