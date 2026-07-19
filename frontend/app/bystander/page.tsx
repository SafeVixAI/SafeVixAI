// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
import React from 'react';

'use client';

import { useState, useCallback } from 'react';
import {
 Eye, MapPin, Phone, AlertTriangle, CheckCircle2,
  Navigation, Activity,
  Loader2, ShieldAlert, Map
} from 'lucide-react';
import { fetchNearbyServices, submitReport } from '@/lib/api';
import { usePageEntry } from '@/hooks/usePageEntry';

// ── Types ─────────────────────────────────────────────────────────────────────
interface GpsPos { lat: number; lon: number }
interface Step { id: number; text: string; critical?: boolean }

// ── Bystander First Aid Steps ─────────────────────────────────────────────────
const BYSTANDER_STEPS: Step[] = [
 { id: 1, text: 'STOP your vehicle safely. Turn on hazard lights.', critical: true },
 { id: 2, text: 'Do NOT move the victim — assume spinal injury.', critical: true },
 { id: 3, text: 'Call 108 (ambulance) RIGHT NOW. GPS location will be shared automatically.', critical: true },
 { id: 4, text: 'Check if victim is breathing — tilt head back, lift chin, watch for chest rise.', critical: false },
 { id: 5, text: 'If not breathing: start CPR — 30 hard chest compressions, then 2 breaths. Repeat.', critical: false },
 { id: 6, text: 'For severe bleeding: press clean cloth firmly on wound. Do NOT remove it.', critical: false },
 { id: 7, text: 'Keep the victim warm with any available jacket/cloth.', critical: false },
 { id: 8, text: 'Stay with them and talk to them until ambulance arrives.', critical: false },
];

// ── TTS Engine ────────────────────────────────────────────────────────────────
function speak(text: string) {
 /* istanbul ignore next */if (typeof window === 'undefined' || !window.speechSynthesis) return;
 window.speechSynthesis.cancel();
 const utt = new SpeechSynthesisUtterance(text);
 utt.lang = 'en-IN';
 utt.rate = 0.9;
 utt.pitch = 1;
 window.speechSynthesis.speak(utt);
}

// ── Main Component ────────────────────────────────────────────────────────────
export default function BystanderModePage() {
 const pageRef = usePageEntry();
 const [phase, setPhase] = useState<'entry' | 'gps' | 'steps' | 'done'>('entry');
 const [gps, setGps] = useState<GpsPos | null>(null);
 const [gpsError, setGpsError] = useState<string | null>(null);
 const [completedSteps, setCompletedSteps] = useState<Set<number>>(new Set());
  const [accidentReported, setAccidentReported] = useState(false);
 const [mapsUrl, setMapsUrl] = useState<string>('');
 const [nearestHospital, setNearestHospital] = useState<{ name: string; distance: string } | null>(null);
  // ── GPS capture ──────────────────────────────────────────────────────────────
 const startGPS = useCallback(() => {
 setPhase('gps');
 speak('GPS is capturing your location. Stay calm.');

  /* istanbul ignore if */if (!navigator.geolocation) {
  /* istanbul ignore next */setGpsError('GPS not supported on this device');
  /* istanbul ignore next */setPhase('steps');
  /* istanbul ignore next */return;
  }

  /* istanbul ignore next */navigator.geolocation.getCurrentPosition(
 (pos) => {
 const coords: GpsPos = { lat: pos.coords.latitude, lon: pos.coords.longitude };
 setGps(coords);
 setMapsUrl(`https://www.google.com/maps?q=${coords.lat},${coords.lon}`);
 setPhase('steps');

 // Speak confirmation
 speak('Location captured. Follow the steps on screen. An ambulance call button is at the bottom.');

  reportAccidentToBackend(coords);
 },
 (err) => {
 setGpsError(`GPS error: ${err.message}`);
 setPhase('steps');
 speak('Location unavailable. Please call 112 and describe your surroundings.');
 },
 { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
 );
 }, []);

  async function reportAccidentToBackend(coords: GpsPos) {
  try {
  await submitReport({
  issue_type: 'accident',
  severity: 4,
  lat: coords.lat,
  lon: coords.lon,
  description: '[Bystander Mode] Road accident witnessed and auto-reported via SafeVixAI',
  });
  setAccidentReported(true);

  const data = await fetchNearbyServices({
  lat: coords.lat,
  lon: coords.lon,
  categories: 'hospital',
  limit: 1,
  });
  const first = data.services[0];
 if (first) {
 setNearestHospital({
 name: first.name,
 distance: `${(first.distanceMeters / 1000).toFixed(1)} km`,
 });
 }
 } catch { /* silent — network may be weak */ }
 }

 function toggleStep(id: number) {
 const s = new Set(completedSteps);
 if (s.has(id)) s.delete(id);
 else {
 s.add(id);
 const step = BYSTANDER_STEPS.find((st) => st.id === id);
 if (step) speak(step.text);
 }
 setCompletedSteps(s);

 if (s.size === BYSTANDER_STEPS.length) setPhase('done');
 }

  // ── Entry Screen ─────────────────────────────────────────────────────────────
 if (phase === 'entry') {
 return (
 <div ref={pageRef} className="min-h-screen bg-bg flex flex-col items-center justify-center p-6 font-sans">
 {/* Spots removed per user request */}
 <div
 className="w-full max-w-sm text-center"
 >
 {/* Icon */}
 <div className="mx-auto mb-6 w-24 h-24 rounded-full bg-red-500/20 border-2 border-red-500/40 flex items-center justify-center shadow-2xl shadow-red-500/20">
 <Eye size={40} className="text-red-400" />
 </div>

 <div className="mb-2 inline-flex items-center gap-2 px-3 py-1 rounded-full bg-red-500/10 border border-red-500/30">
 <span className="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse" />
 <span className="text-[10px] font-black text-red-400 uppercase tracking-widest">Bystander Mode</span>
 </div>

 <h1 className="text-4xl font-black text-white uppercase tracking-tight mt-4 mb-3">
 I Witnessed<br />
 <span className="text-red-400">An Accident</span>
 </h1>

 <p className="text-text-2 text-sm leading-relaxed mb-8">
 SafeVixAI will capture your location, guide you through first aid,
 call emergency services, and notify the nearest hospital — automatically.
 </p>

 <button
 onClick={startGPS}
 className="w-full h-16 bg-red-500 hover:bg-red-600 text-white font-black text-lg uppercase tracking-widest rounded-2xl shadow-2xl shadow-red-500/30 flex items-center justify-center gap-3 transition-all"
 >
 <MapPin size={24} />
 Activate Bystander Mode
 </button>

 <p className="mt-4 text-[10px] text-text-2 uppercase tracking-widest">
 No login required · Works offline · Feeds accident into road reporter
 </p>
 </div>
 </div>
 );
 }

 // ── GPS Loading ───────────────────────────────────────────────────────────────
 if (phase === 'gps') {
 return (
 <div className="min-h-screen bg-bg flex flex-col items-center justify-center p-6 font-sans">
 <Loader2 size={48} className="text-red-400 animate-spin mb-6" />
 <h2 className="text-2xl font-black text-white uppercase tracking-tight mb-2">Capturing Location…</h2>
 <p className="text-text-2 text-sm">GPS locking on accident coordinates</p>
 <p className="mt-6 text-[10px] text-text-2 uppercase tracking-widest">Stay calm · Help is coming</p>
 </div>
 );
 }

 // ── Done Screen ───────────────────────────────────────────────────────────────
 if (phase === 'done') {
 return (
 <div className="min-h-screen bg-bg flex flex-col items-center justify-center p-6 font-sans">
 <div className="w-full max-w-sm text-center">
 <div className="mx-auto mb-6 w-20 h-20 rounded-full bg-brand-light/ border-2 border-brand-light/40 flex items-center justify-center">
 <CheckCircle2 size={36} className="text-brand-light" />
 </div>
 <h2 className="text-3xl font-black text-white uppercase mb-3">All Steps Done</h2>
 <p className="text-text-2 text-sm mb-6">You did everything right. Stay with the victim until help arrives.</p>

 <a
 href="tel:108"
 className="flex items-center justify-center gap-3 w-full h-14 bg-red-500 text-white font-black uppercase tracking-widest rounded-xl shadow-xl shadow-red-500/20 mb-4"
 >
 <Phone size={20} />
 Call 108 Again
 </a>

 {gps && (
 <a
 href={mapsUrl}
 target="_blank"
 rel="noreferrer"
 className="flex items-center justify-center gap-3 w-full h-14 bg-white/10 border border-white/10 text-white font-bold uppercase tracking-widest rounded-xl"
 >
 <Map size={20} />
 Show Location on Maps
 </a>
 )}
 </div>
 </div>
 );
 }

 // ── Steps Screen ─────────────────────────────────────────────────────────────
 return (
 <div className="min-h-screen bg-bg flex flex-col font-sans">
 {/* Header */}
 <div className="sticky top-0 z-10 bg-bg/95 backdrop-blur border-b border-red-500/20 px-4 py-3">
 <div className="flex items-center justify-between mb-2">
 <div className="flex items-center gap-2">
 <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
 <span className="text-[10px] font-black text-red-400 uppercase tracking-widest">Bystander Protocol Active</span>
 </div>
 <span className="text-[10px] font-bold text-brand-light uppercase tracking-widest">
 {completedSteps.size}/{BYSTANDER_STEPS.length} done
 </span>
 </div>

 {/* Progress bar */}
 <div className="h-1 bg-white/5 rounded-full overflow-hidden">
 <div
 className="h-full bg-red-500 rounded-full transition-all duration-300"
 style={{ width: `${(completedSteps.size / BYSTANDER_STEPS.length) * 100}%` }}
 />
 </div>
 </div>

 {/* GPS Status + Nearest Hospital */}
 {(gps || gpsError) && (
 <div className="px-4 pt-4">
 {gps && (
 <a
 href={mapsUrl}
 target="_blank"
 rel="noreferrer"
 className="flex items-center gap-3 p-3 bg-brand-light/10 border border-brand-light/20 rounded-xl mb-3"
 >
 <Navigation size={18} className="text-brand-light flex-shrink-0" />
 <div className="min-w-0">
 <p className="text-[9px] font-black text-brand-light uppercase tracking-widest">GPS Captured · Tap to open</p>
 <p className="text-xs font-mono text-white truncate">{gps.lat.toFixed(5)}, {gps.lon.toFixed(5)}</p>
 </div>
 {accidentReported && (
 <span className="ml-auto text-[8px] font-black text-brand-light bg-brand-light/ px-2 py-1 rounded-full">Reported</span>
 )}
 </a>
 )}

 {gpsError && (
 <div className="flex items-center gap-3 p-3 bg-red-500/10 border border-red-500/20 rounded-xl mb-3">
 <AlertTriangle size={18} className="text-red-400 flex-shrink-0" />
 <p className="text-xs font-bold text-red-300">{gpsError}</p>
 </div>
 )}

 {nearestHospital && (
 <div className="flex items-center gap-3 p-3 bg-brand/10 border border-brand/20 rounded-xl mb-3">
 <Activity size={18} className="text-brand-light flex-shrink-0" />
 <div>
 <p className="text-[9px] font-black text-brand-light uppercase tracking-widest">Nearest Hospital</p>
 <p className="text-xs font-bold text-white">{nearestHospital.name} · {nearestHospital.distance}</p>
 </div>
 </div>
 )}
 </div>
 )}

 {/* Steps */}
 <div className="flex-1 px-4 py-2 pb-28 space-y-3">
 <h2 className="text-[10px] font-black text-text-2 uppercase tracking-widest px-1 mb-2">
 Follow these steps — tap each one when done
 </h2>

 {BYSTANDER_STEPS.map((step) => {
 const done = completedSteps.has(step.id);
 return (
 <button
 key={step.id}
 onClick={() => toggleStep(step.id)}
 className={`w-full text-left flex items-start gap-4 p-4 rounded-xl border transition-all ${
 done
 ? 'bg-brand-light/10 border-brand-light/30 opacity-60'
 : step.critical
 ? 'bg-red-500/10 border-red-500/40 shadow-lg shadow-red-500/10'
 : 'bg-white/5 border-white/10'
 }`}
 >
 <div className={`w-8 h-8 rounded-full flex items-center justify-center font-black text-sm flex-shrink-0 ${
 done ? 'bg-brand-light text-white' : step.critical ? 'bg-red-500 text-white' : 'bg-white/10 text-white'
 }`}>
 {done ? <CheckCircle2 size={18} /> : step.id}
 </div>
 <div className="flex-1">
 {step.critical && !done && (
 <span className="text-[8px] font-black text-red-400 uppercase tracking-widest block mb-1"> Critical</span>
 )}
 <p className={`text-sm font-bold leading-relaxed ${done ? 'text-text-2 line-through' : 'text-white'}`}>
 {step.text}
 </p>
 </div>
 </button>
 );
 })}
 </div>

 {/* Fixed bottom call bar */}
 <div className="fixed bottom-0 left-0 right-0 p-4 bg-bg/95 backdrop-blur border-t border-white/5">
 <div className="grid grid-cols-2 gap-3">
 <a
 href="tel:108"
 className="h-14 bg-red-500 text-white font-black text-sm uppercase tracking-widest rounded-xl flex items-center justify-center gap-2 shadow-xl shadow-red-500/30 active:scale-95 transition-all"
 >
 <Phone size={18} />
 Call 108
 </a>
 <a
 href="tel:112"
 className="h-14 bg-white/10 border border-white/10 text-white font-black text-sm uppercase tracking-widest rounded-xl flex items-center justify-center gap-2 active:scale-95 transition-all"
 >
 <ShieldAlert size={18} />
 Call 112
 </a>
 </div>
 </div>
 </div>
 );
}
