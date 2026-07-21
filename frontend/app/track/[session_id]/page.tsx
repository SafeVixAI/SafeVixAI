'use client';

// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
import React from 'react';

import { useEffect, useRef, useState } from 'react';
import type { RealtimeChannel } from '@supabase/supabase-js';
import { subscribeToTracking, LiveLocation } from '@/lib/live-tracking';
import { getSupabaseBrowserClient } from '@/lib/supabase-auth';
import { gsap } from '@/lib/gsap';
import { useGSAP } from '@gsap/react';
import dynamic from 'next/dynamic';
import { useParams, useSearchParams } from 'next/navigation';
import { 
  Shield, 
  Battery, 
  Phone, 
  ShieldAlert, 
  Navigation, 
  Clock, 
  Heart, 
  Car,
  Loader2
} from 'lucide-react';

// Load map without SSR (Leaflet/MapLibre requires browser)
const EmergencyMap = dynamic(
  () => import('@/components/EmergencyMap').then((m) => m.EmergencyMap),
  { ssr: false, loading: () => <div className="flex-1 bg-surface-1/50 animate-pulse rounded-2xl border border-white/5" /> }
);

interface PageProps {
  params: Promise<{ session_id: string }>;
}

export default function FamilyTrackingPage(_props: PageProps) {
  const params = useParams();
  const session_id = (params as { session_id: string }).session_id;
  const searchParams = useSearchParams();
  const legacyToken = searchParams.get('token') || '';
  
  const containerRef = useRef<HTMLDivElement | null>(null);
  
  const [tokenState, setTokenState] = useState<{ ready: boolean; value: string }>({
    ready: false,
    value: '',
  });
  
  const [location, setLocation] = useState<LiveLocation | null>(null);
  const [animatedCoords, setAnimatedCoords] = useState<{ lat: number; lng: number } | null>(null);
  const [expired, setExpired] = useState(false);
  const [loading, setLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [connectionType, setConnectionType] = useState<'Realtime' | 'Polling' | 'Connecting'>('Connecting');

  // Extract token from hash or query parameter
  useEffect(() => {
    const hashParams = new URLSearchParams(window.location.hash.replace(/^#/, ''));
    setTokenState({ 
      ready: true, 
      value: hashParams.get('token') || legacyToken 
    });
  }, [legacyToken]);

  // Main realtime subscription with REST fallback
  useEffect(() => {
    if (!tokenState.ready) return;
    if (!session_id || !tokenState.value) {
      setExpired(true);
      setLoading(false);
      return;
    }

    let active = true;
    let realtimeChannel: RealtimeChannel | null = null;
    let fallbackPollCleanup: (() => void) | null = null;

    const fetchInitialAndSubscribe = async () => {
      try {
        // 1. Fetch current status from REST endpoint to verify token & get initial state
        const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL || '';
        const res = await fetch(`${apiBase}/api/v1/live-tracking/session/${session_id}`, {
          headers: { Authorization: `Bearer ${tokenState.value}` },
        });

        if (!active) return;

        if (res.status === 404 || res.status === 403) {
          setExpired(true);
          setLoading(false);
          return;
        }

        if (res.ok) {
          const data: LiveLocation = await res.json();
          if (!data.is_active) {
            setExpired(true);
            setLoading(false);
            return;
          }
          
          setLocation(data);
          setAnimatedCoords({ lat: data.latitude, lng: data.longitude });
          setLastUpdated(new Date());
          setLoading(false);

          // 2. Try setting up Supabase Realtime
          const supabase = getSupabaseBrowserClient();
          if (supabase) {
            if (process.env.NODE_ENV !== 'production') console.log('SafeVixAI: Subscribing to Supabase Realtime for session:', session_id);
            setConnectionType('Realtime');
            
            realtimeChannel = supabase
              .channel(`live-tracking:${session_id}`)
              .on(
                'postgres_changes',
                {
                  event: 'UPDATE',
                  schema: 'public',
                  table: 'live_tracking',
                  filter: `session_id=eq.${session_id}`,
                },
                (payload: { new: LiveLocation }) => {
                  if (!active) return;
                  const updated = payload.new;
                  
                  if (!updated.is_active) {
                    setExpired(true);
                    return;
                  }
                  
                  setLocation((prev) => ({
                    session_id: updated.session_id,
                    user_name: updated.user_name || prev?.user_name || 'Emergency Victim',
                    blood_group: updated.blood_group || prev?.blood_group || null,
                    vehicle_number: updated.vehicle_number || prev?.vehicle_number || null,
                    latitude: updated.latitude,
                    longitude: updated.longitude,
                    accuracy: updated.accuracy || null,
                    speed_kmh: updated.speed_kmh != null ? updated.speed_kmh : null,
                    battery_percent: updated.battery_percent != null ? updated.battery_percent : null,
                    is_active: updated.is_active,
                    updated_at: updated.updated_at || new Date().toISOString(),
                  }));
                  setLastUpdated(new Date());
                }
              )
              .subscribe((status) => {
                if (!active) return;
                if (process.env.NODE_ENV !== 'production') console.log(`SafeVixAI: Realtime channel state: ${status}`);
                if (status === 'CHANNEL_ERROR' || status === 'TIMED_OUT') {
                  console.warn('SafeVixAI: Realtime subscription failed. Falling back to HTTP polling.');
                  startPollingFallback();
                }
              });
          } else {
            if (process.env.NODE_ENV !== 'production') console.log('SafeVixAI: Supabase client unavailable. Initializing HTTP polling.');
            startPollingFallback();
          }
        } else {
          startPollingFallback();
        }
      } catch (err) {
        console.error('SafeVixAI: Failed to setup tracking stream:', err);
        if (active) {
          startPollingFallback();
        }
      }
    };

    const startPollingFallback = () => {
      if (fallbackPollCleanup) return;
      setConnectionType('Polling');
      fallbackPollCleanup = subscribeToTracking(
        session_id,
        tokenState.value,
        (loc) => {
          if (!active) return;
          setLocation(loc);
          setAnimatedCoords({ lat: loc.latitude, lng: loc.longitude });
          setLastUpdated(new Date());
          setLoading(false);
        },
        () => {
          if (!active) return;
          setExpired(true);
          setLoading(false);
        },
        5000
      );
    };

    fetchInitialAndSubscribe();

    return () => {
      active = false;
      if (realtimeChannel) {
        getSupabaseBrowserClient()?.removeChannel(realtimeChannel);
      }
      if (fallbackPollCleanup) {
        fallbackPollCleanup();
      }
    };
  }, [session_id, tokenState]);

  // GSAP: Animate the map marker and camera target coordinates smoothly
  useGSAP(() => {
    if (!location) return;

    const currentCoords = animatedCoords || { lat: location.latitude, lng: location.longitude };
    const target = { lat: currentCoords.lat, lng: currentCoords.lng };

    const tween = gsap.to(target, {
      lat: location.latitude,
      lng: location.longitude,
      duration: 1.8,
      ease: 'smooth',
      onUpdate: () => {
        setAnimatedCoords({ lat: target.lat, lng: target.lng });
      },
    });

    return () => {
      tween.kill();
    };
  }, { dependencies: [location?.latitude, location?.longitude] });

  // GSAP: Initial load staggered page transitions
  useGSAP(() => {
    if (loading || expired) return;

    const tl = gsap.timeline();
    tl.fromTo('.anim-header', 
      { y: -30, opacity: 0 }, 
      { y: 0, opacity: 1, duration: 0.6, ease: 'power3.out' }
    )
    .fromTo('.anim-card', 
      { y: 15, opacity: 0 }, 
      { y: 0, opacity: 1, duration: 0.5, stagger: 0.08, ease: 'power3.out' }, 
      '-=0.3'
    )
    .fromTo('.anim-map', 
      { scale: 0.98, opacity: 0 }, 
      { scale: 1, opacity: 1, duration: 0.5, ease: 'power2.out' }, 
      '-=0.2'
    )
    .fromTo('.anim-footer', 
      { y: 30, opacity: 0 }, 
      { y: 0, opacity: 1, duration: 0.5, ease: 'power3.out' }, 
      '-=0.3'
    );
  }, { dependencies: [loading, expired], scope: containerRef });

  const formatTime = (d: Date) =>
    d.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', second: '2-digit' });

  // Facility representing the victim on the map
  const mapFacilities = animatedCoords && location
    ? [
        {
          id: 'victim',
          name: `${location.user_name} (SOS)`,
          type: 'sos',
          coords: [animatedCoords.lat, animatedCoords.lng] as [number, number],
          accentColor: '#ef4444',
          distance: 'LIVE',
        },
      ]
    : [];

  // ── Expired UI ────────────────────────────────────────────────────────────
  if (expired) {
    return (
      <div className="min-h-dvh bg-bg flex items-center justify-center p-4">
        <div className="max-w-md w-full bg-surface-1 border border-border-md rounded-2xl p-8 text-center shadow-2xl relative overflow-hidden group">
          <div className="absolute inset-0 bg-gradient-to-b from-brand/5 to-transparent pointer-events-none" />
          <div className="w-16 h-16 mx-auto rounded-full bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center mb-6">
            <Shield className="text-emerald-400 w-8 h-8" />
          </div>
          <h1 className="text-white font-black text-2xl mb-3 tracking-tight">Session Ended</h1>
          <p className="text-text-2 text-sm leading-relaxed mb-6">
            The emergency live tracking session has been securely closed. The user has marked themselves as safe or the session expired.
          </p>
          <div className="bg-surface-2 border border-white/5 rounded-xl p-4 text-left">
            <span className="text-[10px] font-black tracking-widest text-text-3 uppercase block mb-1">Emergency Advice</span>
            <p className="text-text-2 text-xs leading-relaxed">
              If you still cannot establish communication with the person, please contact the local emergency response services immediately.
            </p>
          </div>
          <a
            href="tel:112"
            className="w-full mt-6 inline-flex items-center justify-center gap-2 h-12 bg-gradient-to-r from-red-600 to-red-700 hover:from-red-500 hover:to-red-600 text-white rounded-xl font-bold uppercase tracking-widest text-xs transition-all shadow-[0_4px_20px_rgba(220,38,38,0.2)]"
          >
            <Phone size={14} /> Call Emergency Helpline (112)
          </a>
        </div>
      </div>
    );
  }

  // ── Loading UI ───────────────────────────────────────────────────────────
  if (loading) {
    return (
      <div className="min-h-dvh bg-bg flex items-center justify-center p-4">
        <div className="max-w-sm w-full text-center space-y-6">
          <div className="relative w-16 h-16 mx-auto">
            <div className="absolute inset-0 rounded-full border-4 border-red-500/10" />
            <Loader2 className="w-16 h-16 text-red-500 animate-spin absolute inset-0" />
          </div>
          <div className="space-y-2">
            <h1 className="text-white font-black text-xl tracking-tight">Accessing Secure Stream...</h1>
            <p className="text-text-2 text-sm">Verifying token signature and resolving GPS coordinates.</p>
          </div>
        </div>
      </div>
    );
  }

  // ── Live Stream UI ────────────────────────────────────────────────────────
  return (
    <div ref={containerRef} className="min-h-dvh bg-bg flex flex-col overflow-x-hidden font-space">
      {/* Aurora Background Ambient Glow */}
      <div className="fixed top-0 left-1/4 w-[500px] h-[500px] bg-red-600/10 rounded-full blur-[140px] pointer-events-none" />
      <div className="fixed bottom-0 right-1/4 w-[400px] h-[400px] bg-brand/5 rounded-full blur-[120px] pointer-events-none" />

      {/* Header */}
      <header className="anim-header border-b border-white/5 bg-surface-1/60 backdrop-blur-md px-4 py-4 flex items-center justify-between z-10">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-red-500/10 border border-red-500/20 flex items-center justify-center shadow-inner">
            <ShieldAlert className="text-red-500 w-5 h-5 animate-pulse" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-text-3 text-[9px] font-black uppercase tracking-widest">
                SafeVix Live Tracking
              </span>
              <span className="px-1.5 py-0.5 rounded text-[8px] font-bold bg-white/5 border border-white/10 text-text-2">
                {connectionType}
              </span>
            </div>
            <div className="text-white font-black text-lg leading-tight tracking-tight">
              {location?.user_name}
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-red-500/10 border border-red-500/20">
          <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse status-dot" />
          <span className="text-red-400 text-[10px] font-black tracking-widest uppercase">LIVE</span>
        </div>
      </header>

      {/* Telemetry Bento Grid */}
      <div className="px-4 py-4 grid grid-cols-3 gap-3 z-10">
        {/* Blood Group */}
        <div className="anim-card bg-surface-1/40 backdrop-blur-md border border-white/5 rounded-2xl p-3 flex flex-col justify-between hover:bg-surface-1/60 transition-all duration-300">
          <div className="flex items-center justify-between mb-2">
            <span className="text-text-3 text-[9px] font-black uppercase tracking-widest">Vitals</span>
            <Heart size={14} className="text-red-500" />
          </div>
          <div>
            <div className="text-[10px] text-text-2 font-bold mb-0.5">Blood Group</div>
            <div className="text-white font-black text-base leading-none">
              {location?.blood_group || '—'}
            </div>
          </div>
        </div>

        {/* Speed */}
        <div className="anim-card bg-surface-1/40 backdrop-blur-md border border-white/5 rounded-2xl p-3 flex flex-col justify-between hover:bg-surface-1/60 transition-all duration-300">
          <div className="flex items-center justify-between mb-2">
            <span className="text-text-3 text-[9px] font-black uppercase tracking-widest">Velocity</span>
            <Navigation size={14} className="text-blue-400 rotate-45" />
          </div>
          <div>
            <div className="text-[10px] text-text-2 font-bold mb-0.5">Speed</div>
            <div className="text-white font-black text-base leading-none">
              {location?.speed_kmh != null ? `${Math.round(location.speed_kmh)} km/h` : '0 km/h'}
            </div>
          </div>
        </div>

        {/* Battery */}
        <div className="anim-card bg-surface-1/40 backdrop-blur-md border border-white/5 rounded-2xl p-3 flex flex-col justify-between hover:bg-surface-1/60 transition-all duration-300">
          <div className="flex items-center justify-between mb-2">
            <span className="text-text-3 text-[9px] font-black uppercase tracking-widest">Device</span>
            <Battery 
              size={14} 
              className={location?.battery_percent != null && location.battery_percent < 20 ? 'text-red-400 animate-pulse' : 'text-emerald-400'} 
            />
          </div>
          <div>
            <div className="text-[10px] text-text-2 font-bold mb-0.5">Battery</div>
            <div className={`font-black text-base leading-none ${
              (location?.battery_percent ?? 100) < 20 ? 'text-red-400' : 'text-white'
            }`}>
              {location?.battery_percent != null ? `${location.battery_percent}%` : '—'}
            </div>
          </div>
        </div>
      </div>

      {/* Map View */}
      <div className="anim-map flex-1 relative min-h-[40vh] mx-4 mb-4 rounded-2xl overflow-hidden border border-white/5 shadow-2xl z-10">
        {animatedCoords && location && (
          <EmergencyMap
            center={[animatedCoords.lat, animatedCoords.lng]}
            facilities={mapFacilities}
            currentLocation={null}
          />
        )}

        {/* Realtime Status Overlay */}
        {lastUpdated && (
          <div className="absolute bottom-4 left-1/2 -translate-x-1/2 z-20 flex items-center gap-2 bg-surface-1/90 text-white text-[10px] font-black uppercase tracking-widest px-4 py-2.5 rounded-xl backdrop-blur-md border border-white/10 shadow-lg">
            <Clock size={12} className="text-brand-light" />
            <span>Updated {formatTime(lastUpdated)}</span>
          </div>
        )}
      </div>

      {/* Vehicle details and Emergency action center */}
      <div className="anim-footer bg-surface-1/60 backdrop-blur-md border-t border-white/5 px-4 py-6 space-y-4 z-10">
        {location?.vehicle_number && (
          <div className="bg-surface-2/40 border border-white/5 rounded-xl p-3 flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <Car size={16} className="text-text-3" />
              <span className="text-xs text-text-2 font-bold">Associated Vehicle</span>
            </div>
            <span className="text-xs font-black text-white bg-white/5 border border-white/10 px-2.5 py-1 rounded-lg uppercase tracking-wider">
              {location.vehicle_number}
            </span>
          </div>
        )}

        <div className="grid grid-cols-2 gap-4">
          <a
            href="tel:112"
            className="flex items-center justify-center gap-2 bg-gradient-to-r from-red-600 to-red-700 hover:from-red-500 hover:to-red-600 text-white text-center py-3.5 rounded-xl font-black text-xs uppercase tracking-widest transition-all btn-interactive shadow-[0_4px_20px_rgba(220,38,38,0.25)]"
          >
            <Phone size={13} /> Call 112
          </a>
          <a
            href="tel:108"
            className="flex items-center justify-center gap-2 bg-gradient-to-r from-orange-600 to-orange-700 hover:from-orange-500 hover:to-orange-600 text-white text-center py-3.5 rounded-xl font-black text-xs uppercase tracking-widest transition-all btn-interactive shadow-[0_4px_20px_rgba(249,115,22,0.25)]"
          >
            <Phone size={13} /> Call 108
          </a>
        </div>

        <p className="text-text-4 text-[9px] font-bold uppercase tracking-[0.1em] text-center">
          Encrypted Live Session · Valid for 4 hours · SafeVix AI Core
        </p>
      </div>
    </div>
  );
}

