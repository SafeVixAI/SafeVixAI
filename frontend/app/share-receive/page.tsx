'use client';

// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
import React from 'react';


import { Suspense, useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { Shield, Loader2, MapPin, ExternalLink } from 'lucide-react';

/**
 * Share Receive Handler — Web Share Target
 *
 * Runs when SafeVixAI receives a share from another app (Google Maps, WhatsApp, etc).
 * Parses GPS coordinates from the shared content and redirects to /locator with
 * pre-loaded location. If no coordinates found, redirects to /locator for manual GPS.
 *
 * Supported share formats:
 *   - Google Maps: https://maps.google.com/?q=13.0827,80.2707
 *   - Google Maps: https://www.google.com/maps/@13.0827,80.2707,17z
 *   - Google Maps: https://goo.gl/maps/xxxxx (plain text with coords)
 *   - Plain text with GPS: "Meeting at 13.0827,80.2707"
 *   - What3Words: "///word.word.word" (redirect to locator for manual entry)
 */

// ── Loading Fallback ──────────────────────────────────────────────────────────

function ShareReceiveLoading() {
  return (
    <div className="min-h-[100dvh] bg-bg flex items-center justify-center p-6">
      <div className="flex flex-col items-center gap-4">
        <Loader2 size={32} className="text-brand-light animate-spin" />
        <p className="text-sm font-bold text-white uppercase tracking-wider">
          Initializing Share Target...
        </p>
      </div>
    </div>
  );
}

// ── Inner Component (uses useSearchParams) ────────────────────────────────────

function ShareReceiveInner() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [status, setStatus] = useState<'parsing' | 'redirecting' | 'no-gps'>('parsing');
  const [parsedCoords, setParsedCoords] = useState<{ lat: string; lon: string } | null>(null);

  useEffect(() => {
    const title = searchParams.get('title') || '';
    const text = searchParams.get('text') || '';
    const link = searchParams.get('link') || searchParams.get('url') || '';

    // Combine all shared text for GPS extraction
    const allText = [title, text, link].join(' ');

    // Pattern 1: Standard decimal GPS (13.0827,80.2707 or 13.0827, 80.2707)
    const gpsMatch = allText.match(
      /(-?\d{1,3}\.\d{3,8})\s*[,\s]\s*(-?\d{1,3}\.\d{3,8})/
    );

    // Pattern 2: Google Maps @lat,lon,zoom format
    const mapsAtMatch = allText.match(
      /@(-?\d{1,3}\.\d+),(-?\d{1,3}\.\d+)/
    );

    // Pattern 3: Google Maps ?q=lat,lon format
    const mapsQMatch = allText.match(
      /[?&]q=(-?\d{1,3}\.\d+),(-?\d{1,3}\.\d+)/
    );

    // Pattern 4: place/lat,lon or dir/lat,lon
    const mapsPlaceMatch = allText.match(
      /(?:place|dir)\/(-?\d{1,3}\.\d+),(-?\d{1,3}\.\d+)/
    );

    const match = mapsQMatch || mapsAtMatch || mapsPlaceMatch || gpsMatch;

    if (match) {
      const lat = match[1];
      const lon = match[2];

      // Validate range
      const latN = parseFloat(lat);
      const lonN = parseFloat(lon);

      if (latN >= -90 && latN <= 90 && lonN >= -180 && lonN <= 180) {
        setParsedCoords({ lat, lon });
        setStatus('redirecting');

        // Short visual delay so user sees the activation animation
        setTimeout(() => {
          router.replace(`/locator?lat=${lat}&lon=${lon}&source=share`);
        }, 800);
        return;
      }
    }

    // No GPS found — redirect to locator for manual GPS capture
    setStatus('no-gps');
    setTimeout(() => {
      router.replace('/locator?source=share');
    }, 1500);
  }, [searchParams, router]);

  return (
    <div className="min-h-[100dvh] bg-bg flex items-center justify-center p-6">
      <h1 className="sr-only">Share Receive</h1>
      {/* Spots removed per user request */}

      {/* Top scan line */}
      <div className="fixed top-0 left-0 right-0 h-0.5 bg-gradient-to-r from-transparent via-brand-light to-transparent opacity-60 animate-pulse" />

      <div className="relative text-center max-w-sm mx-auto">
        {/* Logo */}
        <div className="flex items-center justify-center gap-3 mb-8">
          <div className="w-14 h-14 rounded-xl bg-brand flex items-center justify-center shadow-lg shadow-brand/40">
            <Shield size={28} className="text-white" />
          </div>
          <div className="text-left">
            <p className="text-[11px] font-black text-brand-light uppercase tracking-[0.25em]">SafeVixAI</p>
            <p className="text-[9px] font-bold text-text-2 uppercase tracking-widest">Share Target Active</p>
          </div>
        </div>

        {/* Status */}
        {status === 'parsing' && (
          <div className="flex flex-col items-center gap-4">
            <Loader2 size={32} className="text-brand-light animate-spin" />
            <p className="text-sm font-bold text-white uppercase tracking-wider">
              Parsing shared location...
            </p>
            <p className="text-[10px] text-text-2 uppercase tracking-widest">
              Extracting GPS from shared content
            </p>
          </div>
        )}

        {status === 'redirecting' && parsedCoords && (
          <div className="flex flex-col items-center gap-4">
            <div className="w-16 h-16 rounded-full bg-brand/20 border-2 border-brand-light flex items-center justify-center animate-pulse">
              <MapPin size={28} className="text-brand-light" />
            </div>
            <p className="text-sm font-bold text-white uppercase tracking-wider">
              Location Received
            </p>
            <p className="text-[11px] font-mono text-brand-light">
              {parsedCoords.lat}, {parsedCoords.lon}
            </p>
            <p className="text-[10px] text-text-2 uppercase tracking-widest">
              Activating Emergency Locator...
            </p>
          </div>
        )}

        {status === 'no-gps' && (
          <div className="flex flex-col items-center gap-4">
            <div className="w-16 h-16 rounded-full bg-warning/10 border-2 border-amber-500/30 flex items-center justify-center">
              <ExternalLink size={28} className="text-amber-400" />
            </div>
            <p className="text-sm font-bold text-white uppercase tracking-wider">
              No GPS Coordinates Found
            </p>
            <p className="text-[10px] text-text-2 uppercase tracking-widest leading-relaxed max-w-xs">
              Redirecting to locator — your device GPS will be used instead
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

// ── Page Export with Suspense Boundary ─────────────────────────────────────────

export default function ShareReceivePage() {
  return (
    <Suspense fallback={<ShareReceiveLoading />}>
      <ShareReceiveInner />
    </Suspense>
  );
}