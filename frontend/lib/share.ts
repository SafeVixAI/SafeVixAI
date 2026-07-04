// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

/**
 * share.ts — Outbound Deep Link & Share Generators
 *
 * Generates shareable deep links and handles Web Share API calls
 * for emergency locations, tracking sessions, and road reports.
 */

// ── Base URL ──────────────────────────────────────────────────────────────────

const BASE_URL =
 typeof window !== 'undefined'
 ? window.location.origin
 : (process.env.NEXT_PUBLIC_APP_URL || process.env.NEXT_PUBLIC_VERCEL_URL || '');

// ── Link Generators ───────────────────────────────────────────────────────────

/**
 * Generate a shareable emergency link with GPS coordinates.
 * Opens directly to locator page with pre-loaded location.
 */
export function generateEmergencyLink(lat: number, lon: number): string {
 return `${BASE_URL}/locator?lat=${lat.toFixed(6)}&lon=${lon.toFixed(6)}&source=deeplink`;
}

/**
 * Generate a shareable SOS link that auto-triggers SOS mode.
 */
export function generateSOSLink(lat: number, lon: number): string {
 return `${BASE_URL}/sos?lat=${lat.toFixed(6)}&lon=${lon.toFixed(6)}&mode=sos&source=deeplink`;
}

/**
 * Generate a live tracking link for family members.
 */
export function generateTrackingLink(sessionId: string): string {
 return `${BASE_URL}/track/${sessionId}?source=deeplink`;
}

/**
 * Generate an emergency card link (no login required).
 */
export function generateEmergencyCardLink(userId: string): string {
 return `${BASE_URL}/ec/${userId}`;
}

/**
 * Generate a report deep link — pre-fills location on the report page.
 */
export function generateReportLink(lat: number, lon: number): string {
 return `${BASE_URL}/report?lat=${lat.toFixed(6)}&lon=${lon.toFixed(6)}&source=deeplink`;
}

// ── Web Share API ─────────────────────────────────────────────────────────────

interface ShareOptions {
 title: string;
 text: string;
 url: string;
}

/**
 * Share a link via the native Web Share API (mobile sheet).
 * Falls back to clipboard copy on desktop / unsupported browsers.
 * Returns true if successfully shared/copied.
 */
export async function shareLink(
 title: string,
 url: string,
 text?: string
): Promise<boolean> {
 const shareData: ShareOptions = {
 title,
 text: text || title,
 url,
 };

 // Try native share first (mobile)
 if (typeof navigator !== 'undefined' && navigator.share) {
 try {
 await navigator.share(shareData);
 return true;
 } catch (e) {
 // User cancelled or share failed — try clipboard
 if ((e as Error).name === 'AbortError') return false;
 }
 }

 // Fallback: copy to clipboard
 try {
 await navigator.clipboard.writeText(url);
 return true;
  } catch {
    // Last resort: prompt
    /* istanbul ignore next */
    if (typeof window !== 'undefined') {
 window.prompt('Copy this link:', url);
 }
 return false;
 }
}

/**
 * Share an emergency location via native share or clipboard.
 */
export async function shareEmergencyLocation(
 lat: number,
 lon: number
): Promise<boolean> {
 const url = generateEmergencyLink(lat, lon);
 return shareLink(
 'SafeVixAI Emergency — Help Needed',
 url,
 ` Emergency! I need help at this location. Open SafeVixAI: ${url}`
 );
}

/**
 * Share a live tracking link with family.
 */
export async function shareTrackingSession(
 sessionId: string
): Promise<boolean> {
 const url = generateTrackingLink(sessionId);
 return shareLink(
 'SafeVixAI — Track My Location',
 url,
 `Track my live location on SafeVixAI: ${url}`
 );
}
