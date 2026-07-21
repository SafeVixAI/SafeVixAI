'use client';

// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
import React from 'react';


import { useState, useRef, useCallback, useEffect } from 'react';
import { useAppStore } from '@/lib/store';

import { publicApiWebSocketUrl } from '@/lib/public-env';
import { GROUP_TRACKING_BROADCAST_INTERVAL_MS } from '@/lib/safety-constants';
import { useWebSocket, type WSStatus } from '@/lib/useWebSocket';
import { EmergencyMap } from '@/components/EmergencyMap';
import SystemHeader from '@/components/dashboard/SystemHeader';
import { Loader2, Users, Wifi, WifiOff, RefreshCw } from 'lucide-react';
import { usePageEntry } from '@/hooks/usePageEntry';
import { useShallow } from 'zustand/react/shallow';

interface FamilyMember {
  user_id: string;
  lat: number;
  lon: number;
  timestamp: number;
}

function statusBadge(status: WSStatus, attempt: number): { label: string; color: string; icon: React.ReactNode } {
  switch (status) {
    case 'idle': return { label: 'Not Connected', color: 'text-text-3', icon: <WifiOff size={14} /> };
    case 'connecting': return { label: 'Connecting...', color: 'text-amber-500', icon: <Loader2 size={14} className="animate-spin" /> };
    case 'connected': return { label: 'Live', color: 'text-brand-light', icon: <Wifi size={14} /> };
    case 'disconnected': return { label: 'Disconnected', color: 'text-emergency-dim', icon: <WifiOff size={14} /> };
    case 'reconnecting': return { label: `Reconnecting (${attempt}/${50})...`, color: 'text-amber-500', icon: <RefreshCw size={14} className="animate-spin" /> };
  }
}

export default function TrackingPage() {
  const { gpsLocation, userProfile, authToken } = useAppStore(useShallow((s) => ({ gpsLocation: s.gpsLocation, userProfile: s.userProfile, authToken: s.authToken })));
  const pageRef = usePageEntry();
  const [groupId, setGroupId] = useState('');
  const [userId, setUserId] = useState(userProfile?.name || '');
  const [members, setMembers] = useState<Record<string, FamilyMember>>({});
  const trackingIntervalRef = useRef<NodeJS.Timeout | null>(null);

  const handleMessage = useCallback((data: unknown) => {
    const msg = data as Record<string, unknown>;
    if (msg.user_id && msg.lat && msg.lon) {
      const lat = Number(msg.lat);
      const lon = Number(msg.lon);
      if (!isNaN(lat) && !isNaN(lon)) {
        setMembers((prev) => ({
          ...prev,
          [msg.user_id as string]: {
            user_id: msg.user_id as string,
            lat,
            lon,
            timestamp: Date.now(),
          },
        }));
      }
    }
  }, []);

  const wsRef = useWebSocket({ onMessage: handleMessage });
  const wsStatus = wsRef.status;
  const { send: wsSend } = wsRef;

  useEffect(() => {
    if (wsStatus === 'connected') {
      trackingIntervalRef.current = setInterval(() => {
        /* istanbul ignore if */if (navigator.geolocation) {
          /* istanbul ignore next */navigator.geolocation.getCurrentPosition((pos) => {
            wsSend(JSON.stringify({
              user_id: userId,
              lat: pos.coords.latitude,
              lon: pos.coords.longitude,
            }));
          }, () => {}, { enableHighAccuracy: true, timeout: 5000, maximumAge: 10000 });
        }
      }, GROUP_TRACKING_BROADCAST_INTERVAL_MS);
    } else {
      if (trackingIntervalRef.current) {
        clearInterval(trackingIntervalRef.current);
        trackingIntervalRef.current = null;
      }
    }
  }, [wsStatus, wsSend, userId]);

  const connectToTracking = (e: React.FormEvent) => {
    e.preventDefault();
    if (!groupId || !userId || !authToken) return;

    const wsUrl = publicApiWebSocketUrl(
      `/api/v1/tracking/${groupId}?${new URLSearchParams({ token: authToken })}`,
    );
    wsRef.connect(wsUrl);
  };

  const disconnect = () => {
    wsRef.disconnect();
    setMembers({});
  };

  const badge = statusBadge(wsStatus, wsRef.reconnectAttempt);
  const centerCoords: [number, number] = gpsLocation ? [gpsLocation.lat, gpsLocation.lon] : [28.6139, 77.2090];

  const facilitiesList = Object.values(members).map((member) => ({
    id: member.user_id,
    name: member.user_id === userId ? `${member.user_id} (You)` : member.user_id,
    type: 'family' as const,
    coords: [member.lat, member.lon] as [number, number],
    accentColor: member.user_id === userId ? '#2563eb' : '#10b981',
    distance: 'Live',
  }));

  return (
    <div ref={pageRef} className="min-h-dvh bg-bg dark:bg-surface-1 flex flex-col font-['Inter'] relative overflow-hidden">
      <h1 className="sr-only">Live Family Tracking</h1>
      <SystemHeader title="Live Family Tracking" showBack={true} />

      {wsStatus === 'idle' || wsStatus === 'disconnected' ? (
        <main className="flex-1 flex items-center justify-center p-4 z-10 relative">
          <div className="w-full max-w-md bg-white/80 dark:bg-surface-2/60 backdrop-blur-xl border border-border-md dark:border-white/10 rounded-2xl p-6 shadow-2xl">
            <div className="flex justify-center mb-6">
              <div className="w-16 h-16 bg-brand/10 text-brand dark:text-brand-light rounded-2xl flex items-center justify-center">
                <Users size={32} />
              </div>
            </div>
            <h2 className="text-xl font-black text-center text-text-1 mb-2 uppercase tracking-tight">
              Join Tracking Group
            </h2>
            <p className="text-center text-sm text-text-2 mb-8 font-semibold">
              Enter a secure family code to broadcast and view live GPS locations of your group members.
            </p>

            <form onSubmit={connectToTracking} className="space-y-4">
              <div>
                <label className="block text-[11px] font-bold uppercase tracking-widest text-text-2 mb-1">
                  Family / Group Code
                </label>
                <input
                  required
                  value={groupId}
                  onChange={(e) => setGroupId(e.target.value)}
                  className="w-full bg-surface-1 border border-border-md dark:border-white/10 rounded-xl px-4 py-3 text-sm font-semibold focus:outline-none focus:ring-2 focus:ring-brand"
                  placeholder="e.g. SMITH-FAMILY-24"
                />
              </div>
              <div>
                <label className="block text-[11px] font-bold uppercase tracking-widest text-text-2 mb-1">
                  Your Display Name
                </label>
                <input
                  required
                  value={userId}
                  onChange={(e) => setUserId(e.target.value)}
                  className="w-full bg-surface-1 border border-border-md dark:border-white/10 rounded-xl px-4 py-3 text-sm font-semibold focus:outline-none focus:ring-2 focus:ring-brand"
                  placeholder="e.g. John"
                />
              </div>

              <button
                type="submit"
                className="w-full bg-brand hover:bg-brand/80 text-white py-3.5 rounded-xl font-black text-[12px] uppercase tracking-widest transition-all mt-4"
              >
                Start Tracking
              </button>
            </form>
          </div>
        </main>
      ) : (
        <main className="flex-1 flex flex-col relative z-10 w-full h-full">
          <div className="absolute top-4 left-4 right-4 z-20 flex justify-between items-center bg-white/90 dark:bg-bg/80 backdrop-blur-2xl p-4 rounded-xl border border-border-md dark:border-white/10 shadow-2xl">
            <div>
              <div className="text-[10px] font-bold uppercase tracking-widest text-text-2">
                Active Group
              </div>
              <div className="font-black text-text-1 flex items-center gap-2">
                {groupId}
                <span className={`w-2 h-2 rounded-full ${wsStatus === 'connected' ? 'bg-brand-light animate-pulse' : 'bg-amber-500'}`} />
              </div>
              <div className={`flex items-center gap-1.5 mt-1 text-[10px] font-semibold ${badge.color}`}>
                {badge.icon}
                {badge.label}
              </div>
            </div>

            <button
              onClick={disconnect}
              className="px-4 py-2 bg-emergency/10 text-emergency-dark dark:text-emergency-dim hover:bg-emergency/20 rounded-lg text-[10px] font-bold uppercase tracking-widest transition-all border border-emergency/20"
            >
              Leave
            </button>
          </div>

          <div className="absolute top-28 left-4 z-20 flex flex-col gap-2">
            {Object.values(members).map(member => (
              <div key={member.user_id} className="bg-white/90 dark:bg-bg/80 backdrop-blur-xl px-4 py-2 rounded-lg border border-border-md dark:border-white/10 shadow-xl flex items-center gap-3">
                <div className={`w-3 h-3 rounded-full ${member.user_id === userId ? 'bg-brand' : 'bg-brand-light'} animate-pulse`} />
                <span className="text-xs font-bold text-text-1">
                  {member.user_id === userId ? 'You' : member.user_id}
                </span>
              </div>
            ))}
          </div>

          <div className="flex-1 w-full bg-surface-1 dark:bg-bg">
             <EmergencyMap
                center={centerCoords}
                facilities={facilitiesList}
                currentLocation={
                  gpsLocation
                    ? {
                        lat: gpsLocation.lat,
                        lon: gpsLocation.lon,
                        accuracy: gpsLocation.accuracy,
                        title: 'You',
                        subtitle: wsStatus === 'connected' ? 'Broadcasting live' : 'Reconnecting...',
                      }
                    : null
                }
              />
          </div>
        </main>
      )}
    </div>
  );
}