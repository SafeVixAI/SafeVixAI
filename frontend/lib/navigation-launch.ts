// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

/**
 * navigation-launch.ts — Enterprise Navigation App Launcher
 *
 * Smart launcher for Google Maps, Waze, and Apple Maps with
 * platform detection, user preference persistence, and fallback chain.
 *
 * Usage:
 * import { openBestNavApp, NavApp } from '@/lib/navigation-launch';
 * openBestNavApp({ lat: 13.08, lon: 80.27, name: 'Apollo Hospital' });
 */

// ── Types ──────────────────────────────────────────────────────────────────────

export type NavApp = 'google' | 'waze' | 'apple';

export interface NavDestination {
 lat: number;
 lon: number;
 /** Destination label (hospital name, etc.) */
 name?: string;
}

// ── Storage Key ────────────────────────────────────────────────────────────────

const PREF_KEY = 'svai_preferred_nav_app';

function openExternal(url: string): void {
 const popup = window.open(url, '_blank', 'noopener,noreferrer');
 if (popup) popup.opener = null;
}

// ── Individual Launchers ──────────────────────────────────────────────────────

/**
 * Launch Google Maps with driving directions to destination.
 * Works on Android, iOS, and browser — opens app if installed, else web.
 */
export function openGoogleMaps(dest: NavDestination): void {
 const params = new URLSearchParams({
 api: '1',
 destination: `${dest.lat},${dest.lon}`,
 travelmode: 'driving',
 });
 if (dest.name) params.set('destination_place_id', dest.name);
 openExternal(`https://www.google.com/maps/dir/?${params}`);
}

/**
 * Launch Waze with navigation to destination.
 * Opens Waze app on Android/iOS if installed, else waze.com.
 */
export function openWaze(dest: NavDestination): void {
 const url = `https://waze.com/ul?ll=${dest.lat},${dest.lon}&navigate=yes`;
 openExternal(url);
}

/**
 * Launch Apple Maps with driving directions.
 * Only meaningful on iOS/macOS — opens Maps app natively.
 */
export function openAppleMaps(dest: NavDestination): void {
 const params = new URLSearchParams({
 daddr: `${dest.lat},${dest.lon}`,
 dirflg: 'd', // driving
 });
 if (dest.name) params.set('q', dest.name);
 openExternal(`https://maps.apple.com/?${params}`);
}

// ── Platform Detection ────────────────────────────────────────────────────────

function detectPlatform(): 'ios' | 'android' | 'desktop' {
  /* istanbul ignore next */
  if (typeof navigator === 'undefined') return 'desktop';
 const ua = navigator.userAgent;
 if (/iPad|iPhone|iPod/.test(ua)) return 'ios';
 if (/Android/.test(ua)) return 'android';
 return 'desktop';
}

// ── Smart Launcher ────────────────────────────────────────────────────────────

/**
 * Open the user's preferred navigation app, or auto-detect best option.
 * Priority: user preference → platform default → Google Maps.
 */
export function openBestNavApp(dest: NavDestination): void {
 const pref = getPreferredNavApp();

 switch (pref) {
 case 'waze':
 openWaze(dest);
 break;
 case 'apple':
 openAppleMaps(dest);
 break;
 case 'google':
 default:
 openGoogleMaps(dest);
 break;
 }
}

/**
 * Open a specific navigation app by key.
 */
export function openNavApp(app: NavApp, dest: NavDestination): void {
 switch (app) {
 case 'waze':
 openWaze(dest);
 break;
 case 'apple':
 openAppleMaps(dest);
 break;
 case 'google':
 default:
 openGoogleMaps(dest);
 break;
 }
}

// ── Preference Persistence ────────────────────────────────────────────────────

/**
 * Get the user's preferred navigation app from localStorage.
 * Falls back to platform-appropriate default.
 */
export function getPreferredNavApp(): NavApp {
  /* istanbul ignore next */
  if (typeof localStorage === 'undefined') return 'google';
 const saved = localStorage.getItem(PREF_KEY) as NavApp | null;
 if (saved && ['google', 'waze', 'apple'].includes(saved)) return saved;

 // Platform default
 const platform = detectPlatform();
 return platform === 'ios' ? 'apple' : 'google';
}

/**
 * Set the user's preferred navigation app.
 */
export function setPreferredNavApp(app: NavApp): void {
  /* istanbul ignore next */
  if (typeof localStorage !== 'undefined') {
 localStorage.setItem(PREF_KEY, app);
 }
}

// ── Available Apps List (for UI) ──────────────────────────────────────────────

export const NAV_APPS: { key: NavApp; label: string; emoji: string }[] = [
 { key: 'google', label: 'Google Maps', emoji: '️' },
 { key: 'waze', label: 'Waze', emoji: '' },
 { key: 'apple', label: 'Apple Maps', emoji: '' },
];
