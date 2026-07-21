'use client';

// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team


import React, { useState, useEffect, useRef } from 'react';
import {
  Shield, ChevronDown,
  Heart, Flame, Car, Phone, Zap,
  BookOpen, Activity, Cpu, ArrowRight,
} from 'lucide-react';
import { useTheme } from '@/components/ThemeProvider';
import TopSearch from '@/components/dashboard/TopSearch';
import SystemHeader from '@/components/dashboard/SystemHeader';
import { useUserProfile } from '@/lib/store';
import { useGSAP } from '@gsap/react';
import { gsap } from '@/lib/gsap';
import { useSplitTextEntry } from '@/hooks/useSplitTextEntry';
import { PUBLIC_API_BASE_URL, PUBLIC_CHATBOT_BASE_URL } from '@/lib/public-env';



const CATEGORIES = ['All', 'Medical', 'Fire', 'Accident', 'Criminal'] as const;
type Category = typeof CATEGORIES[number];

interface Protocol {
  id: string;
  title: string;
  subtitle: string;
  category: Exclude<Category, 'All'>;
  accentColor: string;
  glowColor: string;
  icon: React.ReactNode;
  steps: string[];
  callNumber?: string;
  meta?: {
    time: string;
    level: string;
  };
}

const PROTOCOLS: Protocol[] = [
  {
    id: 'cpr',
    title: 'Cardiopulmonary Resuscitation (CPR)',
    subtitle: 'Cardiac arrest intervention for adults & children',
    category: 'Medical',
    accentColor: '#10b981',
    glowColor: 'rgba(16,185,129,0.15)',
    icon: <Heart size={20} />,
    steps: [
      'Check scene safety and tap shoulders — shout "Are you OK?"',
      'Call 112 immediately or ask someone to call',
      'Tilt head back, lift chin, check for breathing (10 sec)',
      'Give 30 chest compressions: hard, fast, center of chest',
      'Give 2 rescue breaths — seal mouth, watch chest rise',
    ],
    callNumber: '108',
    meta: { time: '8-12m', level: 'Critical' }
  },
  {
    id: 'bleeding',
    title: 'Severe Hemorrhage & Bleeding',
    subtitle: 'Tourniquet application and trauma management',
    category: 'Medical',
    accentColor: '#ef4444',
    glowColor: 'rgba(239,68,68,0.15)',
    icon: <Zap size={20} />,
    steps: [
      'Apply firm direct pressure with clean cloth',
      'Elevate wound above heart level if possible',
      'Apply tourniquet 5–7cm above wound for limb bleeding',
      'Note time of application — write on skin',
      'Call 108 and monitor for shock symptoms',
    ],
    callNumber: '108',
    meta: { time: '4-6m', level: 'Fatal' }
  },
  {
    id: 'fire',
    title: 'Fire Emergency Response',
    subtitle: 'Evacuation and containment protocol (RACE)',
    category: 'Fire',
    accentColor: '#ff8c45',
    glowColor: 'rgba(255,140,69,0.15)',
    icon: <Flame size={20} />,
    steps: [
      'RESCUE: Remove anyone in immediate danger',
      'ALERT: Activate fire alarm and shout "Fire!"',
      'CONTAIN: Close all doors to limit fire spread',
      'EVACUATE: Use stairs only. Stay low in smoke',
    ],
    callNumber: '101',
    meta: { time: '2-4m', level: 'High' }
  },
  {
    id: 'accident',
    title: 'Road Accident Response',
    subtitle: 'Scene management and victim stabilization',
    category: 'Accident',
    accentColor: '#3b82f6',
    glowColor: 'rgba(59,130,246,0.15)',
    icon: <Car size={20} />,
    steps: [
      'Park safely 50m ahead, hazard lights ON',
      'Call 112 — give exact location & victim count',
      'Do NOT move victims unless immediate risk exists',
      'If unconscious: put in recovery position',
    ],
    callNumber: '112',
    meta: { time: '10-15m', level: 'Tactical' }
  }
];

export default function EmergencyProtocolsPage() {
  const [activeCategory, setActiveCategory] = useState<Category>('All');
  const [expandedId, setExpandedId] = useState<string | null>('cpr');
  const [mounted, setMounted] = useState(false);
  const { theme } = useTheme();
  const userProfile = useUserProfile();

  // GSAP refs
  const sosCardRef = useRef<HTMLDivElement>(null);
  const callBtnRef = useRef<HTMLAnchorElement>(null);
  const protocolGridRef = useRef<HTMLDivElement>(null);
  const floatingBtnRef = useRef<HTMLButtonElement>(null);
  const titleRef = useSplitTextEntry();

  useEffect(() => {
    setMounted(true);
    document.title = 'Emergency Protocols | SafeVixAI';
    // Pre-warm backend + chatbot for emergency cold-start prevention
    const BACKEND = PUBLIC_API_BASE_URL;
    const CHATBOT = PUBLIC_CHATBOT_BASE_URL;
    Promise.allSettled([
      fetch(`${BACKEND}/health`, { method: 'GET', cache: 'no-store' }),
      fetch(`${CHATBOT}/health`, { method: 'GET', cache: 'no-store' }),
    ]);
  }, []);

  // GSAP Emergency Animations - fast snap
  useGSAP(() => {
    if (!mounted || !sosCardRef.current) return;

    // SOS Card snaps into place
    gsap.fromTo(sosCardRef.current,
      { opacity: 0, scale: 0.95 },
      { opacity: 1, scale: 1, duration: 0.25, ease: 'emergency' }
    );

    // Continuous red glow pulse - signals urgency
    gsap.to(sosCardRef.current, {
      boxShadow: '0 0 45px rgba(239,68,68,0.7), 0 0 0 2px rgba(239,68,68,0.4)',
      scale: 1.01,
      duration: 1.0, yoyo: true, repeat: -1, ease: 'sine.inOut'
    });

    // CALL 112 button attention pulse
    if (callBtnRef.current) {
      gsap.to(callBtnRef.current, {
        scale: 1.02, duration: 0.8,
        yoyo: true, repeat: -1, ease: 'sine.inOut'
      });
    }

    // Floating SOS button pulse
    if (floatingBtnRef.current) {
      gsap.to(floatingBtnRef.current, {
        boxShadow: '0 0 40px rgba(239,68,68,0.6)',
        duration: 1.5, yoyo: true, repeat: -1, ease: 'sine.inOut'
      });
    }
  }, { dependencies: [mounted] });

  // Animate protocol cards on filter change
  useGSAP(() => {
    if (!mounted || !protocolGridRef.current) return;

    const cards = protocolGridRef.current.querySelectorAll('.protocol-card');
    gsap.fromTo(cards,
      { opacity: 0, scale: 0.95, y: 12 },
      { opacity: 1, scale: 1, y: 0, duration: 0.3, stagger: 0.05, ease: 'power2.out' }
    );
  }, { dependencies: [activeCategory, mounted] });

  const filtered = PROTOCOLS.filter(
    p => activeCategory === 'All' || p.category === activeCategory
  );

  const categoryColor: Record<string, string> = {
    Medical: '#10b981',
    Fire: '#ff8c45',
    Accident: '#3b82f6',
    Criminal: '#d4a8ff',
  };

  return (
    <div className={`sv-page sv-aurora relative flex flex-col overflow-x-hidden transition-colors duration-500 ${!mounted ? 'opacity-0' : 'opacity-100'}`}>
      
      {/* ── Unified Tactical Navigation Header ── */}
      <SystemHeader title="Emergency Protocol Terminal" showBack={false} />
      
      <div className="lg:hidden relative z-[100]">
        <TopSearch isMapPage={false} forceShow={true} showBack={false} />
      </div>
      {/* ── Main Protocol Hub ── */}
      <main className="flex-1 w-full max-w-7xl mx-auto pt-28 lg:pt-24 pb-52 px-5 sm:px-12 flex flex-col lg:grid lg:grid-cols-[1.2fr,2fr] lg:gap-14 lg:items-start transition-all duration-500">
        
        {/* ── Left Column: Tactical Control & SOS (Sticky) ── */}
        <aside className="lg:sticky lg:top-28 flex flex-col gap-8">
          {/* Hero Protocol Context */}
          <section className="flex flex-col gap-2">
            <div className="flex flex-wrap items-center gap-3">
              <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-orange-500/10 border border-orange-500/20 w-fit">
                <span className="w-1.5 h-1.5 rounded-full bg-orange-500 animate-pulse"></span>
                <span className="text-[10px] font-semibold text-orange-600 dark:text-orange-400 uppercase tracking-[0.1em] font-space leading-none">Tactical Center</span>
              </div>
              <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-brand-light/10 border border-brand-light/20 w-fit">
                <span className="w-1.5 h-1.5 rounded-full bg-brand-light"></span>
                <span className="text-[10px] font-semibold text-brand dark:text-brand-light uppercase tracking-[0.1em] font-space leading-none">Satellite Lock</span>
              </div>
            </div>
            <div className="flex flex-col">
              <h1 ref={titleRef as React.RefObject<HTMLHeadingElement>} className="text-3xl sm:text-4xl font-black tracking-tight text-text-1 uppercase font-space leading-tight">
                Protocol Terminal
              </h1>
              <p className="max-w-md text-[13px] font-medium text-text-3 mt-2 uppercase tracking-wider opacity-80 leading-relaxed font-space">
                Real-time emergency override & standard hardware-grade guidance. High-gravity environment active.
              </p>
            </div>
          </section>

          {/* Module 1: Hazard Override Terminal (SOS) */}
          <section className="relative group">
            <div 
               ref={sosCardRef}
               className="emergency-sos-card relative rounded-[2.5rem] overflow-hidden p-8 bg-gradient-to-br from-red-600 to-red-900 shadow-2xl shadow-red-600/30 border border-white/10"
            >
              {/* Background Animations */}
              <div className="absolute inset-0 z-0 pointer-events-none">
                <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,rgba(255,255,255,0.1),transparent_70%)] animate-pulse" style={{ animationDuration: '4s' }} />
                <div className="absolute top-0 left-0 w-full h-px bg-gradient-to-r from-transparent via-white/20 to-transparent" />
              </div>

              <div className="relative z-10 flex flex-col gap-6">
                <div className="flex items-center gap-5">
                  <div className="w-16 h-16 rounded-lg bg-white/20 backdrop-blur-md flex items-center justify-center border border-white/20 shadow-xl">
                    <Shield size={32} className="text-white" />
                  </div>
                  <div className="flex flex-col">
                    <span className="text-[10px] font-semibold uppercase tracking-[0.1em] text-red-100/70 mb-1 font-space">Emergency Override</span>
                    <h2 className="text-2xl font-black text-white tracking-tighter uppercase font-space leading-none mb-2">Emergency SOS</h2>
                    <div className="flex items-center gap-2">
                       <span className="w-2 h-2 rounded-full bg-white animate-ping" />
                       <span className="text-[9px] font-semibold text-white uppercase tracking-widest opacity-90">Live Geoloc Sync Active</span>
                    </div>
                  </div>
                </div>

                <div className="flex flex-col gap-3">
                   <a ref={callBtnRef} href="tel:112" className="group/btn relative w-full h-16 px-8 bg-white rounded-lg flex items-center justify-center gap-3 shadow-xl overflow-hidden active:scale-95 transition-all ring-2 ring-white/30 mb-2">
                     <span className="text-red-700 font-black text-sm tracking-[0.1em] uppercase font-space relative z-10">CALL 112 NOW</span>
                     <ArrowRight size={18} className="text-red-700 relative z-10 transition-transform group-hover/btn:translate-x-1" />
                   </a>
                   {/* Emergency Contact Dialer Cards */}
                   {userProfile?.emergencyContacts && userProfile.emergencyContacts.length > 0 ? (
                     <div className="grid grid-cols-1 gap-2 mt-2 w-full">
                       {userProfile.emergencyContacts.map((contact, idx) => (
                         <a 
                           key={idx}
                           href={`tel:${contact.phone}`} 
                           className="group/contact relative w-full p-4 bg-white/10 dark:bg-white/5 border border-white/20 rounded-xl flex items-center justify-between gap-3 shadow-sm hover:bg-white/20 transition-all active:scale-95"
                         >
                           <div className="flex items-center gap-3">
                             <div className="p-2 rounded-lg bg-white/20 text-white">
                               <Phone size={14} />
                             </div>
                             <div className="flex flex-col items-start">
                               <span className="text-[9px] font-semibold text-red-200/70 uppercase tracking-widest leading-none mb-1">{contact.relation}</span>
                               <span className="text-white font-black text-sm uppercase font-space leading-none">{contact.name}</span>
                             </div>
                           </div>
                           <span className="text-[10px] font-bold text-white bg-white/10 px-2.5 py-1 rounded-full font-mono">
                             {contact.phone}
                           </span>
                         </a>
                       ))}
                     </div>
                   ) : userProfile?.emergencyContact ? (
                     <a href={`tel:${userProfile.emergencyContact}`} className="group/btn relative w-full h-14 px-8 bg-brand-light/10 border border-brand-light/30 rounded-lg flex items-center justify-center gap-3 shadow-sm hover:bg-brand-light/20 transition-all active:scale-95">
                       <Phone size={16} className="text-brand-light relative z-10" />
                       <span className="text-brand-light font-black text-xs tracking-[0.1em] uppercase font-space relative z-10">QUICK DIAL: EMERGENCY CONTACT</span>
                     </a>
                   ) : null}
                   <div className="flex items-center justify-between px-2 text-[10px] font-semibold uppercase text-red-200/60 tracking-[0.1em]">
                      <span>Armed & Ready</span>
                      <span>Secure Connection</span>
                   </div>
                </div>
              </div>
            </div>
          </section>
        </aside>

        {/* ── Right Column: Protocol Portfolio ── */}
        <div className="flex flex-col gap-8 pt-8 lg:pt-0">

        {/* Module 2: Tactical Filter Bay */}
        <section className="flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-semibold uppercase tracking-[0.1em] text-text-3 font-space flex items-center gap-2">
              <Activity size={14} className="text-red-500" />
              Filter by Category
            </h3>
            <span className="text-[10px] font-bold text-text-3 font-mono italic">SVA_V4.2_INTEL</span>
          </div>
          
          <div className="flex gap-2.5 overflow-x-auto pb-6 scrollbar-hide -mx-1 px-1" role="radiogroup" aria-label="Filter by emergency category">
            {CATEGORIES.map(cat => {
              const isActive = activeCategory === cat;
              const color = cat === 'All' ? '#0f172a' : categoryColor[cat];
              return (
                <button 
                  key={cat} 
                  onClick={() => setActiveCategory(cat)} 
                  role="radio"
                  aria-checked={isActive}
                  className={`group relative flex-shrink-0 px-6 py-3 rounded-lg text-[10px] font-semibold uppercase tracking-widest transition-all active:scale-90 border-2 ${
                    isActive 
                      ? (cat === 'All' ? 'text-white dark:text-text-1 border-transparent bg-transparent shadow-lg' : 'text-text-1 dark:text-bg border-transparent bg-transparent shadow-lg')
                      : 'bg-white dark:bg-white/5 border-border text-text-3 hover:border-text-3 dark:hover:border-white/10'
                  }`}
                >
                  {isActive && (
                    <div 
                      className="absolute inset-0 rounded-[18px] z-[-1] transition-all duration-300" 
                      style={{ 
                        background: cat === 'All' ? (theme === 'dark' ? '#ffffff' : '#0f172a') : color, 
                        boxShadow: `0 8px 20px ${cat === 'All' ? (theme === 'dark' ? '#ffffff44' : '#0f172a44') : color + '44'}` 
                      }} 
                    />
                  )}
                  {cat}
                </button>
              );
            })}
          </div>
        </section>

        {/* Module 3: Protocol Intelligence folders */}
        <section className="flex flex-col gap-4">
          <div className="flex items-center justify-between px-2">
            <span className="text-[10px] font-semibold text-text-3 uppercase tracking-widest font-space">{filtered.length} INTEL FOLDERS ACCESSED</span>
            <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-brand-light/10 border border-brand-light/20">
               <BookOpen size={10} className="text-brand-light" />
               <span className="text-[9px] font-semibold text-brand-light uppercase tracking-widest">OFFLINE READY</span>
            </div>
          </div>

          <div ref={protocolGridRef} className="grid gap-4 sv-stagger">
              {filtered.map((protocol) => {
                const isExpanded = expandedId === protocol.id;
                return (
                  <ProtocolCard
                    key={protocol.id}
                    protocol={protocol}
                    isExpanded={isExpanded}
                    onToggle={() => setExpandedId(isExpanded ? null : protocol.id)}
                  />
                );
              })}
          </div>
        </section>

          <div className="mt-8 flex flex-col items-center gap-4 py-8">
             <div className="w-12 h-px bg-border" />
             <p className="text-[10px] font-semibold text-text-3 uppercase tracking-[0.1em] font-space opacity-50">Sentinel V4.2 Protocol Feed</p>
          </div>
        </div>
      </main>
      {/* Floating Tactical SOS */}
      <a href="tel:112" className="fixed bottom-[110px] right-6 sm:right-12 z-50">
        <button 
          ref={floatingBtnRef}
          className="sos-button w-16 h-16 bg-red-600 rounded-full flex items-center justify-center shadow-[0_0_30px_rgba(239,68,68,0.5)] text-white relative overflow-hidden hover:scale-110 active:scale-90 transition-transform"
        >
          <span className="absolute inset-0 rounded-full bg-white animate-ping opacity-30" />
          <Phone size={24} className="relative z-10" />
        </button>
      </a>

    </div>
  );
}

// ── Protocol Card Component with GSAP ──
function ProtocolCard({ protocol, isExpanded, onToggle }: {
  protocol: Protocol;
  isExpanded: boolean;
  onToggle: () => void;
}) {
  const contentRef = useRef<HTMLDivElement>(null);
  const chevronRef = useRef<HTMLDivElement>(null);

  useGSAP(() => {
    if (chevronRef.current) {
      gsap.to(chevronRef.current, { rotate: isExpanded ? 180 : 0, duration: 0.2, ease: 'power2.out' });
    }
  }, { dependencies: [isExpanded] });

  // Animate expand/collapse
  useGSAP(() => {
    if (!contentRef.current) return;
    if (isExpanded) {
      gsap.set(contentRef.current, { display: 'block' });
      gsap.fromTo(contentRef.current,
        { height: 0, opacity: 0 },
        { height: 'auto', opacity: 1, duration: 0.3, ease: 'power2.out' }
      );
      // Stagger steps in
      const steps = contentRef.current.querySelectorAll('.step-item');
      gsap.fromTo(steps,
        { x: -10, opacity: 0 },
        { x: 0, opacity: 1, duration: 0.2, stagger: 0.08, ease: 'power2.out', delay: 0.1 }
      );
    } else {
      gsap.to(contentRef.current, {
        height: 0, opacity: 0, duration: 0.2, ease: 'power2.in',
        onComplete: () => { if (contentRef.current) gsap.set(contentRef.current, { display: 'none' }); }
      });
    }
  }, { dependencies: [isExpanded] });

  return (
    <div
      className={`protocol-card sv-card-premium group relative rounded-lg sm:rounded-xl transition-all duration-500 border border-border overflow-hidden shadow-sm ${isExpanded ? 'bg-white dark:bg-surface-1 ring-1 ring-border shadow-2xl' : 'bg-white/60 dark:bg-black/20 hover:bg-white dark:hover:bg-white/5'}`}
    >
      {/* Header: Intel Brief */}
      <button onClick={onToggle} className="w-full flex items-center p-5 sm:p-7 text-left gap-5 relative z-10 transition-colors">
        <div className="w-14 h-14 sm:w-16 sm:h-16 rounded-lg flex items-center justify-center shrink-0 border transition-all" style={{ backgroundColor: protocol.glowColor, borderColor: `${protocol.accentColor}33`, color: protocol.accentColor }}>
          {protocol.icon}
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[9px] font-semibold uppercase tracking-widest px-1.5 py-0.5 rounded-md" style={{ backgroundColor: `${protocol.accentColor}22`, color: protocol.accentColor }}>{protocol.category}</span>
            {protocol.meta && <span className="text-[9px] font-semibold text-text-3 uppercase tracking-widest">{protocol.meta.level} PRIORITY</span>}
          </div>
          <h3 className="text-lg font-black dark:text-white uppercase font-space tracking-tight leading-none mb-1.5 truncate">{protocol.title}</h3>
          <p className="text-xs font-bold text-text-2 dark:text-text-2 truncate opacity-80">{protocol.subtitle}</p>
        </div>

        <div className="flex flex-col items-end gap-3 shrink-0">
          <div className="hidden sm:flex gap-1">
             {[...Array(3)].map((_, j) => (
               <div key={j} className="w-1 h-3 rounded-full bg-surface-3" style={{ backgroundColor: j === 0 ? protocol.accentColor : '' }} />
             ))}
          </div>
          <div ref={chevronRef}>
            <ChevronDown size={20} className="text-text-3 group-hover:text-text-1 transition-colors" />
          </div>
        </div>
      </button>

      {/* Content: Active Guidance HUD */}
      <div ref={contentRef} style={{ overflow: 'hidden', display: isExpanded ? 'block' : 'none' }}>
         <div className="px-5 sm:px-8 pb-8 pt-2">
           <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-border to-transparent" />
           
           <div className="mt-6 flex flex-col gap-6">
             <div className="flex items-center justify-between">
                <label className="text-[10px] font-semibold text-text-3 uppercase tracking-widest font-space flex items-center gap-2">
                   <Cpu size={14} className="text-red-500/60" />
                   Step-by-Step Tactical Guide
                </label>
                {protocol.meta && <span className="text-[10px] font-mono text-brand-light tracking-tighter">EST: {protocol.meta.time}</span>}
             </div>

             <div className="space-y-4">
               {protocol.steps.map((step, i) => (
                 <div key={i} className="step-item flex gap-4 items-start group/step">
                    <div className="w-8 h-8 rounded-xl flex items-center justify-center shrink-0 text-xs font-semibold transition-all" style={{ backgroundColor: protocol.glowColor, color: protocol.accentColor }}>{i + 1}</div>
                    <div className="flex-1 pt-1.5 border-b border-border pb-4 group-last/step:border-none">
                       <p className="text-sm font-bold text-text-2 leading-relaxed font-mono tracking-tight">{step}</p>
                    </div>
                 </div>
               ))}
             </div>

             {protocol.callNumber && (
               <a 
                 href={`tel:${protocol.callNumber}`}
                 className="relative w-full h-14 rounded-lg flex items-center justify-center gap-3 overflow-hidden shadow-xl hover:brightness-110 transition-all active:scale-95"
                 style={{ background: protocol.glowColor }}
               >
                  <Phone size={20} style={{ color: protocol.accentColor }} />
                  <span className="font-black text-[11px] tracking-[0.1em] uppercase font-space" style={{ color: protocol.accentColor }}>Dispatch {protocol.callNumber}</span>
               </a>
             )}
           </div>
         </div>
      </div>
    </div>
  );
}