'use client';

// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
import React from 'react';


import { useState, useEffect, useRef } from 'react';
import dynamic from 'next/dynamic';
import { useGSAP } from '@gsap/react';
import { gsap } from '@/lib/gsap';
import { 
  HeartPulse, Activity, Flame, Bone, Droplets, 
  Search, ArrowLeft, X, CheckCircle2, 
  Phone, Clock, AlertTriangle, ShieldAlert,
  ChevronRight, Camera, Globe,
  Menu, SearchX,
} from 'lucide-react';



import { track } from '@/lib/analytics';
import { useAppStore } from '@/lib/store';
import { useTranslation } from 'react-i18next';

const CameraViewport = dynamic(() => import('@/components/first-aid/CameraViewport'), { ssr: false })

interface Guide {
  id: string;
  title: string;
  subtitle: string;
  accent: string;
  icon: string;
  iconType: 'filled' | 'outlined';
  steps: string[];
}

const TypingText = ({ text, onComplete }: { text: string; onComplete?: () => void }) => {
  const [displayedText, setDisplayedText] = useState("");
  const index = useRef(0);

  useEffect(() => {
    index.current = 0;
    setDisplayedText("");
  }, [text]);

  useEffect(() => {
    if (index.current < text.length) {
      const timeout = setTimeout(() => {
        setDisplayedText((prev) => prev + text[index.current]);
        index.current += 1;
      }, 10);
      return () => clearTimeout(timeout);
    } else if (onComplete) {
      onComplete();
    }
  }, [displayedText, text, onComplete]);

  return <span>{displayedText}</span>;
};



export function FirstAidClient({ guides }: { guides: Record<string, Guide> }) {
  const { t } = useTranslation();
  const [searchQuery, setSearchQuery] = useState('');
  const [activeGuide, setActiveGuide] = useState<string | null>(null);
  const [completedSteps, setCompletedSteps] = useState<Set<number>>(new Set());
  const [emergencyMode, setEmergencyMode] = useState(false);
  const [cameraError, setCameraError] = useState<string | null>(null);
  const [isScanning, setIsScanning] = useState(false);
  const [scrollProgress, setScrollProgress] = useState(0);
  const modalScrollRef = useRef<HTMLDivElement>(null);
  const setSystemSidebarOpen = useAppStore((state) => state.setSystemSidebarOpen);
  
  useEffect(() => {
    document.title = `${t('nav.first_aid', 'First Aid')} | SafeVixAI`;
  }, [t]);

  useEffect(() => {
    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setActiveGuide(null);
    };
    window.addEventListener('keydown', handleEsc);
    return () => window.removeEventListener('keydown', handleEsc);
  }, []);

  const handleModalScroll = () => {
    if (modalScrollRef.current) {
      const { scrollTop, scrollHeight, clientHeight } = modalScrollRef.current;
      const progress = (scrollTop / (scrollHeight - clientHeight)) * 100;
      setScrollProgress(progress);
    }
  };

  const toggleStep = (idx: number) => {
    const newSteps = new Set(completedSteps);
    if (newSteps.has(idx)) newSteps.delete(idx);
    else newSteps.add(idx);
    setCompletedSteps(newSteps);
  };

  const guideKeys = Object.keys(guides).filter(key => 
    guides[key].title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    guides[key].subtitle.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const filteredGuideKeys = guideKeys.filter(key => !emergencyMode || ['cpr', 'choking', 'bleeding'].includes(key));

  return (
    <div className="sv-page sv-aurora relative flex flex-col h-[100dvh] overflow-hidden bg-surface-1">
      {/* ── Page Header Bar (Sticky) ── */}
      <header className="fixed top-0 left-0 w-full z-[100] bg-surface-1/80 backdrop-blur-2xl border-b border-border shadow-sm px-4 lg:px-8 h-[56px] flex items-center justify-between">
        <div className="flex items-center gap-3">
          <button
            onClick={() => setSystemSidebarOpen(true)}
            className="p-1.5 rounded-full hover:bg-surface-3 text-text-2 lg:hidden transition-colors"
            aria-label="Open navigation menu"
          >
            <Menu size={20} />
          </button>
          <h1 className="text-[20px] font-semibold text-[--emergency] uppercase tracking-tight font-space flex items-center gap-2">
            <ShieldAlert size={20} />
            {t('first_aid.hud_title', 'First Aid HUD')}
          </h1>
        </div>

        <button 
          onClick={() => setEmergencyMode(!emergencyMode)}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full border transition-all duration-300 font-bold text-[10px] uppercase tracking-widest ${
            emergencyMode 
              ? 'bg-red-500 text-white border-red-400 shadow-[0_0_20px_rgba(239,68,68,0.4)] animate-pulse' 
              : 'bg-surface-2 dark:bg-white/5 text-text-3 border-border dark:border-white/10 hover:bg-surface-3 dark:hover:bg-white/10'
          }`}
        >
          <AlertTriangle size={12} className={emergencyMode ? 'animate-pulse' : ''} />
          {emergencyMode ? t('first_aid.emergency_active', 'Emergency Active') : t('first_aid.normal_mode', 'Normal Mode')}
        </button>
      </header>
      
      <main className="flex-1 overflow-y-auto px-4 sm:px-6 pt-20 pb-44">
        <div className="max-w-7xl mx-auto">
          {/* ── Premium HUD Header ── */}
          <div className="mb-8 flex flex-col sm:flex-row sm:items-end justify-between gap-4">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse"></span>
                <span className="text-[10px] font-semibold uppercase tracking-[0.1em] text-emergency font-space">{t('first_aid.emergency_guide', 'Emergency Guide')}</span>
              </div>
              <p className="text-text-3 font-medium text-sm leading-relaxed">{t('first_aid.guide_subtitle', 'Select a category below to initiate standard first-aid treatment procedures.')}</p>
            </div>
          </div>
          {/* ── Search HUD ── */}
          {!emergencyMode && (
            <section 
              className="mb-10 relative group"
            >
              <div className="flex items-center justify-between mb-3 px-2">
                <div className="flex items-center gap-2">
                  <Globe size={14} className="text-brand dark:text-brand-light" />
                  <span className="text-[10px] font-semibold uppercase tracking-[0.25em] text-brand dark:text-brand-light font-space">{t('first_aid.system_operational', 'System Status: Operational')}</span>
                </div>
                <div className="flex items-center gap-1">
                   <div className="w-1 h-1 rounded-full bg-text-2" />
                   <span className="text-[8px] font-bold text-text-3 uppercase tracking-widest">{t('first_aid.mission_ready', 'L-09 Mission Ready')}</span>
                </div>
              </div>
              <div className="absolute -inset-0.5 bg-gradient-to-r from-brand/10 to-brand-light/10 rounded-lg blur opacity-20 transition duration-500 group-hover:opacity-40"></div>
              <div className="relative bg-white/60 dark:bg-surface-2/40 backdrop-blur-xl p-3 sm:p-4 rounded-lg flex items-center gap-4 border border-border/80 dark:border-white/5 focus-within:border-brand/30 transition-all duration-300">
                <Search className="text-text-3 dark:text-text-3 shrink-0" size={18} />
                <input 
                  className="bg-transparent border-none text-text-1 dark:text-text-1 placeholder:text-text-3/40 focus:ring-0 w-full text-base focus:outline-none font-medium" 
                  placeholder={t('first_aid.search_placeholder', 'Search emergency protocol...')} 
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
              </div>
            </section>
          )}

        {/* ── Protocol Grid ── */}
        <ProtocolGrid
          guideKeys={filteredGuideKeys}
          guides={guides}
          emergencyMode={emergencyMode}
          onGuideSelect={(key) => { setActiveGuide(key); setCompletedSteps(new Set()); track.firstAidViewed(key); }}
        />

        {/* ── AI Vision Assessment: Live Simulation ── */}
        <section className="mt-12 mb-20 sv-glass sv-scan-line rounded-[2.5rem] p-6 sm:p-10 shadow-sm">
          <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-6 mb-10">
            <div>
              <div className="flex items-center gap-2 mb-3">
                <Camera size={14} className="text-brand dark:text-brand-light" />
                <span className="text-[10px] font-semibold uppercase tracking-[0.25em] text-brand dark:text-brand-light font-space">{t('first_aid.diagnostic_module', 'Diagnostic Module SVX-1')}</span>
              </div>
              <h3 className="text-3xl font-black text-text-1 dark:text-white tracking-tight font-space uppercase mb-2">{t('first_aid.ai_vision_title', 'AI Vision Assessment')}</h3>
              <p className="text-text-3 dark:text-text-3 font-medium text-sm max-w-lg leading-relaxed">{t('first_aid.ai_vision_subtitle', 'Real-time identification of trauma, bleeding patterns, and skeletal anomalies using multi-spectral computer vision.')}</p>
            </div>
            
            <button 
              onClick={() => setIsScanning(true)}
              className="bg-brand hover:bg-brand/80 shadow-[0_8px_25px_var(--brand-dim)] px-8 py-4 rounded-lg text-white font-black uppercase tracking-widest text-[10px] flex items-center gap-3 active:scale-95 transition-all w-fit"
            >
              <Camera size={18} />
              {t('first_aid.invoke_scan', 'Invoke Full Scan')}
            </button>
          </div>
          
          <div className="relative rounded-[2rem] overflow-hidden group border border-border dark:border-white/10 bg-bg aspect-video sm:aspect-[16/9] sm:h-auto max-h-[500px] shadow-2xl">
            {/* Camera Viewport */}
            {isScanning ? (
              <CameraViewport onError={setCameraError} />
            ) : (
              <div className="absolute inset-0 flex flex-col items-center justify-center text-text-3 gap-4 bg-bg/40">
                <Camera size={48} className="opacity-20" />
                <span className="text-[10px] font-bold uppercase tracking-widest text-text-3">{t('first_aid.scanner_offline', 'Scanner Offline. Invoke full scan to initialize.')}</span>
              </div>
            )}

            {/* HUD Overlay - Only show if camera is NOT errored and is scanning */}
            {!cameraError && isScanning && (
              <div className="absolute inset-0 pointer-events-none z-10 p-6 flex flex-col justify-between">
                <div className="flex justify-between items-start">
                  <div className="flex gap-2">
                    <div className="w-10 h-10 border-t border-l border-brand/40" />
                    <div className="flex flex-col mt-2">
                      <span className="text-[7px] font-semibold text-brand dark:text-brand-light/60 font-mono tracking-tighter uppercase">Initializing...</span>
                    </div>
                  </div>
                  <div className="w-10 h-10 border-t border-r border-brand/40" />
                </div>

                {/* Center Crosshair */}
                <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 flex items-center justify-center">
                  <div className="w-24 h-24 border border-brand/10 rounded-full animate-ping opacity-20" />
                  <div className="w-16 h-px bg-brand/30" />
                  <div className="h-16 w-px bg-brand/30" />
                </div>

                <div className="flex justify-between items-end">
                  <div className="w-10 h-10 border-b border-l border-brand/40" />
                  <div className="bg-black/80 backdrop-blur-md px-5 py-4 rounded-lg border border-white/5 flex items-center gap-4">
                     <div className="flex flex-col">
                       <span className="text-[8px] font-semibold text-text-3 uppercase tracking-widest mb-0.5">{t('first_aid.focus_state', 'Focus State')}</span>
                       <span className="text-[10px] font-bold text-white font-mono">{t('first_aid.awaiting_input', 'AWAITING_INPUT')}</span>
                     </div>
                     <div className="w-2 h-2 rounded-full bg-brand/80 animate-pulse shadow-[0_0_10px_var(--brand-dim)]" />
                  </div>
                  <div className="w-10 h-10 border-b border-r border-brand/40" />
                </div>
              </div>
            )}
          </div>
        </section>
      </div>
    </main>

      {/* ── Active Guide Modal: Survival HUD ── */}
          <GuideModal
            activeGuide={activeGuide}
            guides={guides}
            completedSteps={completedSteps}
            toggleStep={toggleStep}
            scrollProgress={scrollProgress}
            modalScrollRef={modalScrollRef}
            handleModalScroll={handleModalScroll}
            onClose={() => setActiveGuide(null)}
          />
    </div>
  );
}

// ── ProtocolGrid: GSAP stagger grid with progressive disclosure ──
function ProtocolGrid({ guideKeys, guides, emergencyMode, onGuideSelect }: {
  guideKeys: string[];
  guides: Record<string, Guide>;
  emergencyMode: boolean;
  onGuideSelect: (_key: string) => void;
}) {
  const { t } = useTranslation();
  const gridRef = useRef<HTMLDivElement>(null);
  const extraCardsRef = useRef<HTMLDivElement>(null);
  const [expanded, setExpanded] = useState(false);

  useGSAP(() => {
    if (!gridRef.current) return;
    const cards = gridRef.current.querySelectorAll('.protocol-card');
    gsap.fromTo(cards,
      { opacity: 0, y: 20, scale: 0.95 },
      { opacity: 1, y: 0, scale: 1, duration: 0.35, stagger: 0.08, ease: 'power2.out' }
    );
  }, { scope: gridRef, dependencies: [guideKeys.length, emergencyMode] });

  useGSAP(() => {
    if (!extraCardsRef.current || !expanded) return;
    gsap.fromTo(
      extraCardsRef.current.querySelectorAll('.protocol-card'),
      { opacity: 0, y: 16 },
      { opacity: 1, y: 0, duration: 0.28, stagger: 0.06, ease: 'power2.out' }
    );
  }, { scope: extraCardsRef, dependencies: [expanded] });

  const initialKeys = guideKeys.slice(0, 4);
  const extraKeys = guideKeys.slice(4);

  const renderCard = (key: string) => {
    const guide = guides[key];
    const isCritical = ['cpr', 'bleeding'].includes(key);
    const titleText = t(`first_aid.${guide.id}.title`, guide.title);
    const subtitleText = t(`first_aid.${guide.id}.subtitle`, guide.subtitle);
    return (
      <button
        type="button"
        key={key}
        onClick={() => onGuideSelect(key)}
        aria-label={`Open ${titleText} first aid guide`}
        className={`protocol-card sv-card-premium group cursor-pointer relative overflow-hidden rounded-xl p-6 sm:p-8 text-left transition-all duration-300 border ${
          isCritical 
            ? 'bg-white dark:bg-surface-2 border-red-500/20 shadow-[0_20px_50px_rgba(239,68,68,0.1)] dark:shadow-[0_20px_50px_rgba(0,0,0,0.3)]' 
            : 'bg-white/60 dark:bg-surface-1/40 backdrop-blur-md border-border/80 dark:border-white/5 hover:border-brand/30'
        } ${emergencyMode && key === 'cpr' ? 'md:col-span-2 lg:col-span-3 py-12' : ''}`}
      >
        <div className="absolute top-4 right-6 flex items-center gap-2">
          {isCritical && (
            <div className="bg-red-500/10 text-red-500 px-2 py-0.5 rounded-full text-[9px] font-semibold tracking-widest uppercase border border-red-500/20 flex items-center gap-1">
              <AlertTriangle size={10} />
              {t('first_aid.priority_p0', 'Priority P0')}
            </div>
          )}
          <div className="bg-brand-light/10 text-brand dark:text-brand-light px-2 py-0.5 rounded-full text-[9px] font-semibold tracking-widest uppercase border border-brand-light/20 flex items-center gap-1">
            <div className="w-1 h-1 rounded-full bg-brand-light animate-pulse" />
            {t('first_aid.offline_badge', 'Offline')}
          </div>
        </div>
        <div className="flex flex-col h-full justify-between gap-8 relative z-10">
          <div className="flex flex-col gap-5">
            <div className={`p-4 rounded-lg w-fit transition-transform group-hover:scale-110 duration-500 ${
              isCritical ? 'bg-red-500/10 text-red-500' : 'bg-brand/10 text-brand dark:text-brand-light'
            }`}>
              {key === 'cpr' && <HeartPulse size={emergencyMode ? 48 : 32} />}
              {key === 'choking' && <Activity size={32} />}
              {key === 'bleeding' && <Droplets size={32} />}
              {key === 'burns' && <Flame size={32} />}
              {key === 'fractures' && <Bone size={32} />}
            </div>
            <div>
              <h2 className={`font-black tracking-tight text-text-1 dark:text-white mb-2 font-space uppercase ${
                emergencyMode && key === 'cpr' ? 'text-4xl sm:text-5xl' : 'text-2xl'
              }`}>{titleText}</h2>
              <p className={`text-text-3 font-medium leading-relaxed ${
                emergencyMode && key === 'cpr' ? 'text-lg max-w-xl' : 'text-sm'
              }`}>{subtitleText}</p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <span className={`inline-flex items-center gap-2 px-5 py-2.5 rounded-xl font-bold transition-all ${
              isCritical 
                ? 'bg-red-500 text-white shadow-lg shadow-red-500/25 hover:shadow-red-500/40' 
                : 'bg-surface-3 dark:bg-white/10 text-text-1 dark:text-white hover:bg-surface-1 dark:hover:bg-white/20'
            }`}>
              {t('first_aid.start_guide', 'Start Guide')} <ChevronRight size={16} />
            </span>
          </div>
        </div>
        <div className="absolute -bottom-6 -right-6 opacity-[0.03] dark:opacity-[0.05] group-hover:opacity-10 transition-opacity duration-700 pointer-events-none">
          {key === 'cpr' && <HeartPulse size={180} />}
          {key === 'bleeding' && <Droplets size={180} />}
        </div>
      </button>
    );
  };

  if (guideKeys.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-center">
        <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-surface-3">
          <SearchX size={24} className="text-text-3" />
        </div>
        <p className="text-sm font-semibold text-text-1">{t('first_aid.no_match', 'No protocols match your search')}</p>
        <p className="mt-1 text-xs text-text-2">{t('first_aid.try_different', 'Try a different keyword or browse all categories')}</p>
      </div>
    );
  }

  return (
    <div ref={gridRef} className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {initialKeys.map(renderCard)}
      
      {extraKeys.length > 0 && (
        <div ref={extraCardsRef} className={`col-span-full ${expanded ? 'block' : 'hidden'}`}>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 w-full pt-6">
            {extraKeys.map(renderCard)}
          </div>
        </div>
      )}

      {extraKeys.length > 0 && (
        <div className="col-span-full flex justify-center mt-6">
          <button
            onClick={() => setExpanded(!expanded)}
            className="px-6 py-2.5 rounded-full border border-border bg-surface-2 text-text-2 hover:text-text-1 font-bold text-xs uppercase tracking-widest transition-all"
          >
            {expanded ? t('first_aid.show_less', 'Show Less Protocols') : t('first_aid.show_all', 'Show All Protocols')}
          </button>
        </div>
      )}

      {!emergencyMode && (
        <div className="group cursor-pointer relative bg-gradient-to-br from-surface-3 to-surface-1 dark:from-surface-2 dark:to-bg rounded-xl p-8 border border-border dark:border-white/5 flex items-center justify-between col-span-1 md:col-span-2 lg:col-span-1 hover:border-brand/20 transition-all shadow-xl shadow-black/20">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <Clock size={14} className="text-brand-light" />
              <span className="text-[10px] font-semibold text-brand-light uppercase tracking-widest font-space">{t('first_aid.inventory_hud', 'Inventory HUD')}</span>
            </div>
            <h3 className="text-xl font-black text-text-1 dark:text-white font-space uppercase">{t('first_aid.kit_title', 'First Aid Kit')}</h3>
            <p className="text-text-3 text-xs font-medium">{t('first_aid.kit_subtitle', 'Inventory checklist & alerts')}</p>
          </div>
          <button className="bg-surface-3 dark:bg-white/10 p-4 rounded-lg text-text-1 dark:text-white group-hover:bg-brand/80 group-hover:text-white transition-all duration-300">
            <ChevronRight size={24} />
          </button>
        </div>
      )}
    </div>
  );
}

// ── GuideModal: GSAP animated modal with step stagger + CPR metronome ──
function GuideModal({ activeGuide, guides, completedSteps, toggleStep, scrollProgress, modalScrollRef, handleModalScroll, onClose }: {
  activeGuide: string | null;
  guides: Record<string, Guide>;
  completedSteps: Set<number>;
  toggleStep: (_idx: number) => void;
  scrollProgress: number;
  modalScrollRef: React.RefObject<HTMLDivElement | null>;
  handleModalScroll: () => void;
  onClose: () => void;
}) {
  const { t } = useTranslation();
  const overlayRef = useRef<HTMLDivElement>(null);
  const stepsRef = useRef<HTMLDivElement>(null);
  const progressBarRef = useRef<HTMLDivElement>(null);
  const metronomeRef = useRef<HTMLDivElement>(null);
  const previousFocusRef = useRef<HTMLElement | null>(null);

  useEffect(() => {
    if (!activeGuide) return;
    previousFocusRef.current = document.activeElement as HTMLElement | null;
    overlayRef.current?.focus();

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        onClose();
        return;
      }
      if (event.key !== 'Tab') return;

      const dialog = overlayRef.current;
      if (!dialog) return;
      const focusable = dialog.querySelectorAll<HTMLElement>(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
      );
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (!first || !last) return;

      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      previousFocusRef.current?.focus();
    };
  }, [activeGuide, onClose]);

  // GSAP entry animation
  useGSAP(() => {
    if (!activeGuide || !overlayRef.current) return;
    gsap.fromTo(overlayRef.current,
      { opacity: 0 },
      { opacity: 1, duration: 0.25, ease: 'power2.out' }
    );
  }, [activeGuide]);

  // GSAP step stagger
  useGSAP(() => {
    if (!activeGuide || !stepsRef.current) return;
    const steps = stepsRef.current.querySelectorAll('.step-item');
    gsap.fromTo(steps,
      { opacity: 0, x: -10 },
      { opacity: 1, x: 0, duration: 0.25, stagger: 0.08, delay: 0.2, ease: 'power2.out' }
    );
  }, [activeGuide]);

  // CPR metronome GSAP
  useGSAP(() => {
    if (!metronomeRef.current || activeGuide !== 'cpr') return;
    const el = metronomeRef.current;
    gsap.to(el, {
      scale: 1.4, opacity: 0.3,
      duration: 0.3, yoyo: true, repeat: -1, ease: 'sine.inOut'
    });
  }, [activeGuide]);

  // Progress bar
  useGSAP(() => {
    if (!progressBarRef.current) return;
    gsap.to(progressBarRef.current, { scaleX: scrollProgress / 100, transformOrigin: 'left', duration: 0.1 });
  }, [scrollProgress]);

  if (!activeGuide || !guides[activeGuide]) return null;

  const guide = guides[activeGuide];

  return (
    <div
      ref={overlayRef}
      tabIndex={-1}
      role="dialog"
      aria-modal="true"
      aria-labelledby="first-aid-modal-title"
      className="fixed inset-0 z-[100] bg-[#f8fafc]/90 dark:bg-bg/95 backdrop-blur-xl flex flex-col overflow-hidden"
    >
      <div className="p-4 sm:p-6 border-b border-border dark:border-white/10 flex items-center justify-between bg-white/50 dark:bg-bg/50 backdrop-blur-md">
        <div className="flex items-center gap-4">
          <button onClick={onClose} className="p-2 rounded-full hover:bg-surface-3 dark:hover:bg-white/5 text-text-2 dark:text-text-3 transition-colors" aria-label="Close first aid guide">
            <ArrowLeft size={20} />
          </button>
          <div>
            <div className="flex items-center gap-2 mb-0.5">
              <span className="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse" />
              <span className="text-[9px] font-semibold uppercase tracking-[0.1em] text-red-600 dark:text-red-400 font-space">{t('first_aid.live_protocol', 'Live Protocol')}</span>
            </div>
            <h2 id="first-aid-modal-title" className="text-xl sm:text-2xl font-black text-text-1 dark:text-white font-space uppercase">{t(`first_aid.${guide.id}.title`, guide.title)}</h2>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <a href="tel:112" onClick={() => track.emergencyCallMade('112')} aria-label="Call 112 emergency services" className="flex items-center gap-2 px-4 py-2 bg-red-500 text-white rounded-full font-bold text-xs uppercase tracking-widest shadow-lg shadow-red-500/25 active:scale-95 transition-transform">
            <Phone size={14} /> {t('first_aid.call_112', 'Call 112')}
          </a>
          <button onClick={onClose} className="p-2 text-text-3 hover:text-text-2 dark:hover:text-white" aria-label="Close first aid guide">
            <X size={24} />
          </button>
        </div>
      </div>

      <div className="h-1 bg-red-500/20 w-full relative">
        <div ref={progressBarRef} className="absolute inset-y-0 left-0 bg-red-500" style={{ width: 0 }} />
      </div>

      <div ref={modalScrollRef} onScroll={handleModalScroll} className="flex-1 overflow-y-auto px-4 sm:px-6 py-8">
        <div className="max-w-3xl mx-auto space-y-8">
          <div className="bg-white dark:bg-surface-2 rounded-xl p-6 sm:p-8 border border-border dark:border-white/5 shadow-xl">
            <div className="flex items-start gap-6">
              <div className="p-5 rounded-lg bg-red-500/10 text-red-500">
                <h3 className="text-sm font-semibold text-red-600 dark:text-red-400 uppercase tracking-widest font-space mb-2">{t('first_aid.instructions_label', 'Instructions')}</h3>
                <p className="text-lg sm:text-xl text-text-2 dark:text-text-1 font-medium leading-relaxed">
                  <TypingText text={t(`first_aid.${guide.id}.subtitle`, guide.subtitle)} />
                </p>
              </div>
            </div>
 
            {activeGuide === 'cpr' && (
              <div className="mt-8 pt-8 border-t border-border-md dark:border-white/5 flex flex-col items-center">
                <p className="text-[10px] font-semibold uppercase tracking-widest text-text-3 mb-4">{t('first_aid.metronome_title', 'Compression Metronome (100 BPM)')}</p>
                <div className="relative">
                  <div ref={metronomeRef} className="w-24 h-24 rounded-full bg-red-500/20 border-2 border-red-500/40 flex items-center justify-center">
                    <div className="w-12 h-12 rounded-full bg-red-500 shadow-[0_0_30px_rgba(239,68,68,0.5)]" />
                  </div>
                  <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                    <span className="text-white font-black text-sm uppercase">{t('first_aid.metronome_pulse', 'PULSE')}</span>
                  </div>
                </div>
                <p className="mt-4 text-xs font-bold text-red-600 dark:text-red-400 uppercase tracking-widest animate-pulse">{t('first_aid.push_hard_fast', 'Push Hard, Push Fast')}</p>
              </div>
            )}
          </div>

          <div ref={stepsRef} className="space-y-4">
            <div className="flex items-center justify-between px-2">
              <h3 className="text-xs font-semibold text-text-3 uppercase tracking-[0.25em] font-space">{t('first_aid.sequential_actions', 'Sequential Actions')}</h3>
              <span className="text-[10px] font-semibold text-brand-light uppercase tracking-widest">
                {t('first_aid.complete_count', { completed: completedSteps.size, total: guide.steps.length, defaultValue: `${completedSteps.size} / ${guide.steps.length} Complete` })}
              </span>
            </div>
            {guide.steps.map((step, idx) => {
              const stepText = t(`first_aid.${guide.id}.steps.${idx}`, step);
              return (
                <button
                  type="button"
                  key={idx}
                  className={`step-item group w-full cursor-pointer p-5 sm:p-6 rounded-lg border text-left transition-all duration-300 flex gap-5 items-start ${
                    completedSteps.has(idx)
                      ? 'bg-brand-light/10 text-brand border-brand-light/20 dark:text-brand-light dark:border-brand-light/20 opacity-60 scale-[0.98]'
                      : 'bg-white dark:bg-surface-2/60 dark:hover:bg-surface-2 border-border dark:border-white/5 text-text-1'
                  }`}
                  onClick={() => toggleStep(idx)}
                  aria-pressed={completedSteps.has(idx)}
                  // source is static Guide object, not user input — safe for aria-label context
                  aria-label={`Step ${idx + 1}: ${stepText.split(/<[^>]*>/).join('').substring(0, 60)}`}
                >
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center font-black flex-shrink-0 text-xs transition-colors ${
                    completedSteps.has(idx) ? 'bg-brand-light text-white' : 'bg-surface-2 dark:bg-white/10 text-text-3'
                  }`}>
                    {completedSteps.has(idx) ? <CheckCircle2 size={16} /> : idx + 1}
                  </div>
                  <div className="flex-1 space-y-1">
                    <p className="font-bold leading-relaxed">{stepText}</p>
                    {idx === 0 && !completedSteps.has(idx) && (
                      <div className="flex items-center gap-1.5 text-red-600 dark:text-red-400 animate-pulse">
                        <AlertTriangle size={12} />
                        <span className="text-[10px] font-semibold uppercase tracking-widest">{t('first_aid.critical_foundation', 'Critical Foundation')}</span>
                      </div>
                    )}
                  </div>
                </button>
              );
            })}
          </div>

          <div className="pt-8 pb-12 flex flex-col sm:flex-row gap-4 items-center justify-center">
            <button onClick={onClose} aria-label="Close first aid guide" className="w-full sm:w-auto px-10 py-4 bg-surface-3 dark:bg-white/10 text-text-1 dark:text-white font-black uppercase tracking-widest text-xs rounded-lg active:scale-95 transition-all">
              {t('first_aid.terminate_protocol', 'Terminate Protocol')}
            </button>
            <a href="tel:108" onClick={() => track.emergencyCallMade('108')} aria-label="Call 108 ambulance service" className="w-full sm:w-auto px-10 py-4 bg-red-500 text-white font-black uppercase tracking-widest text-xs rounded-lg shadow-xl shadow-red-500/20 animate-pulse flex items-center justify-center gap-2 active:scale-95 transition-all">
              <Phone size={16} /> {t('first_aid.emergency_hotline', 'Emergency Hotline')}
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}