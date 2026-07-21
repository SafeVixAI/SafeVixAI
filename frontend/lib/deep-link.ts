// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

/**
 * deep-link.ts — Centralized Deep Link Context Parser
 *
 * Parses URL search params on any SafeVixAI page to extract
 * GPS coordinates, activation mode, source attribution, and
 * session identifiers from deep links, share targets, and QR codes.
 *
 * Usage:
 *   'use client';
 *   import { useDeepLinkContext } from '@/lib/deep-link';
 *   const { lat, lon, mode, source } = useDeepLinkContext();
 */

'use client';

import { useSearchParams } from 'next/navigation';
import { useMemo } from 'react';

// ── Types ──────────────────────────────────────────────────────────────────────

export type ActivationSource = 'share' | 'shortcut' | 'qr' | 'deeplink' | null;
export type ActivationMode = 'sos' | 'track' | 'report' | 'locator' | null;

export interface DeepLinkContext {
  /** Latitude from URL param — validated [-90, 90] */
  lat: number | null;
  /** Longitude from URL param — validated [-180, 180] */
  lon: number | null;
  /** Activation mode: sos, track, report, locator */
  mode: ActivationMode;
  /** Indian state code for challan (e.g. TN, KA, MH) */
  state: string | null;
  /** MV Act section number for challan calculator */
  section: string | null;
  /** How the user arrived: share, shortcut, qr, deeplink */
  source: ActivationSource;
  /** Live tracking session ID */
  sessionId: string | null;
  /** Whether valid GPS coordinates were provided */
  hasLocation: boolean;
}

// ── Validation Helpers ────────────────────────────────────────────────────────

function parseValidLat(raw: string | null): number | null {
  if (!raw) return null;
  const n = parseFloat(raw);
  if (isNaN(n) || n < -90 || n > 90) return null;
  return n;
}

function parseValidLon(raw: string | null): number | null {
  if (!raw) return null;
  const n = parseFloat(raw);
  if (isNaN(n) || n < -180 || n > 180) return null;
  return n;
}

function parseMode(raw: string | null): ActivationMode {
  if (!raw) return null;
  const valid: ActivationMode[] = ['sos', 'track', 'report', 'locator'];
  return valid.includes(raw as ActivationMode) ? (raw as ActivationMode) : null;
}

function parseSource(raw: string | null): ActivationSource {
  if (!raw) return null;
  const valid: ActivationSource[] = ['share', 'shortcut', 'qr', 'deeplink'];
  return valid.includes(raw as ActivationSource) ? (raw as ActivationSource) : null;
}

// ── Hook ──────────────────────────────────────────────────────────────────────

/**
 * React hook that parses the current URL search params into a
 * strongly-typed DeepLinkContext. Safe to call on any page — returns
 * nulls for missing/invalid params.
 */
export function useDeepLinkContext(): DeepLinkContext {
  const searchParams = useSearchParams();

  return useMemo(() => {
    const lat = parseValidLat(searchParams.get('lat'));
    const lon = parseValidLon(searchParams.get('lon'));

    return {
      lat,
      lon,
      mode: parseMode(searchParams.get('mode')),
      state: searchParams.get('state'),
      section: searchParams.get('section'),
      source: parseSource(searchParams.get('source')),
      sessionId: searchParams.get('session'),
      hasLocation: lat !== null && lon !== null,
    };
  }, [searchParams]);
}

// ── Static Parser (for non-React contexts) ────────────────────────────────────

/**
 * Parse deep link context from a URL string directly.
 * Use in service workers, API routes, or non-component code.
 */
export function parseDeepLink(url: string): DeepLinkContext {
  /* istanbul ignore next */const base = process.env.NEXT_PUBLIC_APP_URL || process.env.NEXT_PUBLIC_VERCEL_URL || (typeof window !== 'undefined' ? window.location.origin : '');
  const params = new URL(url, base).searchParams;
  const lat = parseValidLat(params.get('lat'));
  const lon = parseValidLon(params.get('lon'));

  return {
    lat,
    lon,
    mode: parseMode(params.get('mode')),
    state: params.get('state'),
    section: params.get('section'),
    source: parseSource(params.get('source')),
    sessionId: params.get('session'),
    hasLocation: lat !== null && lon !== null,
  };
}
