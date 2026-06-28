// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

import { CRASH_DEBOUNCE_MS, CRASH_THRESHOLD_G, STANDARD_GRAVITY_MS2 } from './safety-constants';

/**
 * SafeVixAI Crash Detection (Web/PWA)
 * 
 * Uses the DeviceMotionEvent API to detect sudden G-force spikes indicative of an accident.
 * Standard gravity is ~9.81 m/s^2. A moderate crash is > 10G (~98 m/s^2).
 */

const CRASH_THRESHOLD_MS2 = CRASH_THRESHOLD_G * STANDARD_GRAVITY_MS2;

// To avoid double-triggering
let isCrashDetected = false;

type CrashCallback = (force: number) => void;
let listeners: CrashCallback[] = [];

// H9 FIX: Track whether the devicemotion listener is already registered
let motionListenerRegistered = false;

/**
 * Handle incoming device motion data.
 */
function handleDeviceMotion(event: DeviceMotionEvent) {
  if (isCrashDetected) return;

  const { accelerationIncludingGravity } = event;
  if (!accelerationIncludingGravity) return;

  const x = accelerationIncludingGravity.x || 0;
  const y = accelerationIncludingGravity.y || 0;
  const z = accelerationIncludingGravity.z || 0;

  // Calculate total acceleration magnitude
  const magnitude = Math.sqrt(x * x + y * y + z * z);

  if (magnitude >= CRASH_THRESHOLD_MS2) {
    isCrashDetected = true;
    listeners.forEach((callback) => callback(magnitude));

    setTimeout(() => {
      isCrashDetected = false;
    }, CRASH_DEBOUNCE_MS);
  }
}

/**
 * Requests permission for iOS devices. Call this from a user gesture handler.
 */
export async function requestCrashPermission(): Promise<boolean> {
  /* istanbul ignore next */
if (typeof window === 'undefined') return false;
  if (typeof DeviceMotionEvent === 'undefined') return false;
  
  if (typeof (DeviceMotionEvent as unknown as { requestPermission?: () => Promise<PermissionState> }).requestPermission === 'function') {
    try {
      const permissionState = await (DeviceMotionEvent as unknown as { requestPermission: () => Promise<PermissionState> }).requestPermission();
      return permissionState === 'granted';
    } catch (e) {
      console.error('Error requesting DeviceMotion permission:', e);
      return false;
    }
  }
  return true;
}

/**
 * Initializes real DeviceMotion listeners if supported.
 * Note: iOS 13+ requires user permission to access DeviceMotionEvent.
 *
 * H9 FIX: Deduplicates callback registration — prevents accumulating duplicate
 * listeners if startCrashDetection is called multiple times with the same callback.
 */
export async function startCrashDetection(onCrashDetected: CrashCallback) {
  /* istanbul ignore next */
if (typeof window === 'undefined') return;
  if (typeof DeviceMotionEvent === 'undefined') return;
  
  // H9 FIX: Prevent duplicate listener registration
  if (listeners.includes(onCrashDetected)) return;
  listeners.push(onCrashDetected);

  // Only register the devicemotion handler once
  if (motionListenerRegistered) return;

  window.addEventListener('devicemotion', handleDeviceMotion, true);
  motionListenerRegistered = true;
}

export function stopCrashDetection(onCrashDetected: CrashCallback) {
  /* istanbul ignore next */
if (typeof window === 'undefined') return;
  
  listeners = listeners.filter((cb) => cb !== onCrashDetected);
  if (listeners.length === 0 && motionListenerRegistered) {
    window.removeEventListener('devicemotion', handleDeviceMotion, true);
    motionListenerRegistered = false;
  }
}

export function simulateCrashDemo() {
  if (isCrashDetected) return;
  
  isCrashDetected = true;
  listeners.forEach((callback) => callback(CRASH_THRESHOLD_MS2 + 10));

  setTimeout(() => {
    isCrashDetected = false;
  }, CRASH_DEBOUNCE_MS);
}
