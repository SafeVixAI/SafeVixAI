// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

'use client';

import React, { useState, useEffect, useRef, useMemo } from 'react';
import { useGSAP } from '@gsap/react';
import { gsap } from '@/lib/gsap';
import {
  Car, Truck, Bike, Bus, AlertTriangle,
  Scale, MapPin,
  ArrowRight, Activity, Zap, Clipboard,
  CheckCircle, RefreshCw, ShieldCheck, AlertOctagon, FileText,
  Sliders, Plus, Check, Mail
} from 'lucide-react';
import TopSearch from '@/components/dashboard/TopSearch';
import SystemHeader from '@/components/dashboard/SystemHeader';
import { useAppStore } from '@/lib/store';
import useSWR from 'swr';
import {
  calculateChallan,
  syncGarage,
  predictFineLiability,
  draftDisputeAppeal,
  VehicleGarageItem,
  DisputeDraftResponse
} from '@/lib/api';
import { loadChallanMetadata } from '@/lib/challan-metadata';
import { useShallow } from 'zustand/react/shallow';
import { track } from '@/lib/analytics';
import { useSwipe } from '@/hooks/useSwipe';
import { useTranslation } from 'react-i18next';

const STATES = [
  'Tamil Nadu (TN)',
  'Delhi (DL)',
  'Maharashtra (MH)',
  'Karnataka (KA)',
  'Uttar Pradesh (UP)',
  'West Bengal (WB)',
];

// Mapped to backend violation_codes
const VIOLATIONS = [
  { id: '183', label: 'Speeding (>20km/h Limit)', mva: 'Section 112/183', max: '4000' },
  { id: '179', label: 'Disobedience / Red Light', mva: 'Section 179', max: '4000' },
  { id: '185', label: 'Section 185 - Drunk driving', mva: 'Section 185', max: '15000 + Imprisonment', danger: 'Up to 6 months imprisonment' },
  { id: '181', label: 'Driving Without License', mva: 'Section 3/181', max: '10000 + 3 Months' },
  { id: '194D', label: 'No Seatbelt/Helmet', mva: 'Section 129/194D', max: '2000 + Disqualification' },
];

const VEHICLE_CLASSES = [
  { id: '2W', icon: <Bike size={28} />, title: '2-Wheeler', subtitle: 'Motorcycle / Scooter' },
  { id: '4W', icon: <Car size={28} />, title: 'Car/LMV', subtitle: 'Light Motor Vehicle' },
  { id: 'HTV', icon: <Truck size={28} />, title: 'Truck', subtitle: 'Heavy Goods Vehicle' },
  { id: 'BUS', icon: <Bus size={28} />, title: 'Bus/COMM', subtitle: 'Public Transport' },
];

type ActiveTab = 'calculator' | 'garage' | 'telemetry' | 'dispute';

export default function ChallanPage() {
  const { t } = useTranslation('challan');
  const [activeTab, setActiveTab] = useState<ActiveTab>('calculator');

  // Use shared store instead of local state so values don't reset upon tab change
  const {
    challanState,
    setChallanState,
    garageVehicles,
    lastSyncedGarage,
    riskAnalysis,
    setGarageVehicles,
    setLastSyncedGarage,
    setRiskAnalysis
  } = useAppStore(useShallow((s) => ({
    challanState: s.challanState,
    setChallanState: s.setChallanState,
    garageVehicles: s.garageVehicles,
    lastSyncedGarage: s.lastSyncedGarage,
    riskAnalysis: s.riskAnalysis,
    setGarageVehicles: s.setGarageVehicles,
    setLastSyncedGarage: s.setLastSyncedGarage,
    setRiskAnalysis: s.setRiskAnalysis
  })));

  // Backwards compatibility for old cached local storage values
  const violationId = (challanState.violation === 'dui') ? '185' :
                      (challanState.violation === 'speeding') ? '183' :
                      (challanState.violation === 'nolicense') ? '181' :
                      (challanState.violation === 'helmet_seatbelt') ? '194D' :
                      (challanState.violation === 'redlight') ? '179' :
                      challanState.violation;

  const vehicleId = challanState.vehicle.toUpperCase();
  const { jurisdiction, isRepeat } = challanState;

  const stateCodeMatch = jurisdiction.match(/\((.*?)\)/);
  const stateCode = stateCodeMatch ? stateCodeMatch[1] : 'TN';

  const [showDetailToast, setShowDetailToast] = useState(false);
  const { data: metadata } = useSWR('challan-metadata', loadChallanMetadata, {
    revalidateOnFocus: false,
  });
  const violationOptions = metadata?.violations?.length ? metadata.violations : VIOLATIONS;
  const stateOptions = metadata?.states?.length ? metadata.states.map((state) => state.label) : STATES;

  // Swipe section navigation
  const [swipeSection, setSwipeSection] = useState(0);
  const violationRef = useRef<HTMLElement>(null);
  const vehicleSectionRef = useRef<HTMLElement>(null);
  const paramsRef = useRef<HTMLElement>(null);
  const insightRef = useRef<HTMLDivElement>(null);
  const swipeSections = useMemo(() => [violationRef, vehicleSectionRef, paramsRef, insightRef], []);

  const { onTouchStart: swipeStart, onTouchEnd: swipeEnd } = useSwipe({
    onSwipeLeft: () => {
      if (swipeSection < swipeSections.length - 1) {
        const next = swipeSection + 1;
        setSwipeSection(next);
        swipeSections[next].current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    },
    onSwipeRight: () => {
      if (swipeSection > 0) {
        const prev = swipeSection - 1;
        setSwipeSection(prev);
        swipeSections[prev].current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    },
  });

  // GSAP refs
  const fineRef = useRef<HTMLHeadingElement>(null);
  const resultCardRef = useRef<HTMLElement>(null);
  const dangerRef = useRef<HTMLDivElement>(null);
  const toastRef = useRef<HTMLDivElement>(null);
  const toggleRef = useRef<HTMLDivElement>(null);
  const vehicleGridRef = useRef<HTMLDivElement>(null);

  // Tab dynamic containers GSAP
  const tabContentRef = useRef<HTMLDivElement>(null);

  useEffect(() => { document.title = t('challan.page_title', 'Challan Calculator | SafeVixAI'); }, [t]);

  // GSAP: Toggle animation
  useGSAP(() => {
    if (!toggleRef.current) return;
    gsap.to(toggleRef.current, {
      x: isRepeat ? 22 : 2,
      duration: 0.2,
      ease: 'bounce',
    });
  }, { dependencies: [isRepeat] });

  // GSAP: Vehicle cards stagger
  useGSAP(() => {
    if (!vehicleGridRef.current) return;
    gsap.fromTo(vehicleGridRef.current.children,
      { opacity: 0, y: 12 },
      { opacity: 1, y: 0, duration: 0.3, stagger: 0.06, ease: 'power2.out' }
    );
  }, { scope: vehicleGridRef, dependencies: [activeTab] });

  // GSAP: Toast
  useGSAP(() => {
    if (!toastRef.current) return;
    if (showDetailToast) {
      gsap.fromTo(toastRef.current,
        { opacity: 0, y: 10 },
        { opacity: 1, y: 0, duration: 0.2 }
      );
    } else {
      gsap.to(toastRef.current, { opacity: 0, y: 10, duration: 0.2 });
    }
  }, { dependencies: [showDetailToast] });

  // GSAP: Tab Transition
  useGSAP(() => {
    if (!tabContentRef.current) return;
    gsap.fromTo(tabContentRef.current,
      { opacity: 0, x: 20 },
      { opacity: 1, x: 0, duration: 0.35, ease: 'power2.out' }
    );
  }, { dependencies: [activeTab] });

  const activeViolation = violationOptions.find(v => v.id === violationId) || violationOptions[0];

  const { data: result, isLoading } = useSWR(
    ['challan', violationId, vehicleId, stateCode, isRepeat],
    () => calculateChallan({
      violation_code: activeViolation.id,
      vehicle_class: vehicleId,
      state_code: stateCode,
      is_repeat: isRepeat
    }),
    { keepPreviousData: true }
  );

  const finalFine = result?.amount_due ?? 0;

  // Track calculation event
  useEffect(() => {
    if (result) {
      track.challanCalculated(
        stateCode,
        activeViolation.mva,
        finalFine,
        isRepeat
      );
    }
  }, [result, stateCode, activeViolation.mva, finalFine, isRepeat]);

  // GSAP: Animate fine amount on change
  useGSAP(() => {
    if (!fineRef.current || activeTab !== 'calculator') return;

    const obj = { val: 0 };
    gsap.to(obj, {
      val: finalFine,
      duration: 1.5,
      ease: 'power2.out',
      onUpdate: () => {
        if (fineRef.current) {
          fineRef.current.innerText = `Rs. ${Math.round(obj.val).toLocaleString('en-IN')}`;
        }
      }
    });

    gsap.fromTo(fineRef.current,
      { opacity: 0, scale: 0.9 },
      { opacity: 1, scale: 1, duration: 0.3, ease: 'power2.out' }
    );
  }, { dependencies: [finalFine, activeTab] });

  // GSAP: Danger badge
  useGSAP(() => {
    if (!dangerRef.current) return;
    if (activeViolation.danger) {
      gsap.fromTo(dangerRef.current,
        { opacity: 0, y: 10 },
        { opacity: 1, y: 0, duration: 0.3, ease: 'power2.out' }
      );
    }
  }, { dependencies: [activeViolation.danger, activeTab] });

  // ════════════════════════════════════════════════════════════
  // 1. GARAGE TAB STATE & LOGIC
  // ════════════════════════════════════════════════════════════
  const [vehicleNo, setVehicleNo] = useState('');
  const [syncing, setSyncing] = useState(false);
  const [syncError, setSyncError] = useState<string | null>(null);

  const handleSync = async (e: React.FormEvent) => {
    e.preventDefault();
    setSyncing(true);
    setSyncError(null);
    try {
      const res = await syncGarage(vehicleNo.trim() || undefined);
      setGarageVehicles(res.vehicles);
      setLastSyncedGarage(Date.now());
    } catch (err: any) {
      setSyncError(err.response?.data?.detail || err.message || 'Sync failed');
    } finally {
      setSyncing(false);
    }
  };

  // ════════════════════════════════════════════════════════════
  // 2. TELEMETRY TAB STATE & LOGIC
  // ════════════════════════════════════════════════════════════
  const [speedingEvents, setSpeedingEvents] = useState(5);
  const [harshBraking, setHarshBraking] = useState(2);
  const [nightDriving, setNightDriving] = useState(180);
  const [totalKm, setTotalKm] = useState(1500);
  const [predicting, setPredicting] = useState(false);
  const [predictError, setPredictError] = useState<string | null>(null);

  const handlePredict = async () => {
    setPredicting(true);
    setPredictError(null);
    try {
      const res = await predictFineLiability({
        vehicle_number: vehicleNo || 'TN-01-AB-1234',
        state_code: stateCode,
        telemetry: {
          speeding_events: speedingEvents,
          harsh_braking_events: harshBraking,
          night_driving_minutes: nightDriving,
          total_km_driven: totalKm,
        }
      });
      setRiskAnalysis(res);
    } catch (err: any) {
      setPredictError(err.response?.data?.detail || err.message || 'Prediction failed');
    } finally {
      setPredicting(false);
    }
  };

  // ════════════════════════════════════════════════════════════
  // 3. DISPUTE TAB STATE & LOGIC
  // ════════════════════════════════════════════════════════════
  const [challanRefNo, setChallanRefNo] = useState('CH-2026-9876');
  const [disputeFine, setDisputeFine] = useState(2000);
  const [disputeCode, setDisputeCode] = useState('183');
  const [mitigatingFactors, setMitigatingFactors] = useState(
    'Speed sign was completely obscured by overgrown trees, making visibility impossible.'
  );
  const [draftingDispute, setDraftingDispute] = useState(false);
  const [disputeResponse, setDisputeResponse] = useState<DisputeDraftResponse | null>(null);
  const [disputeError, setDisputeError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  const handleDraft = async (e: React.FormEvent) => {
    e.preventDefault();
    setDraftingDispute(true);
    setDisputeError(null);
    try {
      const res = await draftDisputeAppeal({
        challan_ref: challanRefNo,
        violation_code: disputeCode,
        fine_amount: Number(disputeFine),
        mitigating_factors: mitigatingFactors,
      });
      setDisputeResponse(res);
    } catch (err: any) {
      setDisputeError(err.response?.data?.detail || err.message || 'Drafting failed');
    } finally {
      setDraftingDispute(false);
    }
  };

  const handleCopy = () => {
    if (disputeResponse?.appeal_letter) {
      /* istanbul ignore next */navigator.clipboard.writeText(disputeResponse.appeal_letter);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleEmailAppeal = () => {
    if (disputeResponse?.appeal_letter) {
      const subject = encodeURIComponent(`Challan Dispute Appeal - Ref: ${challanRefNo}`);
      const body = encodeURIComponent(disputeResponse.appeal_letter);
      window.location.href = `mailto:?subject=${subject}&body=${body}`;
    }
  };

  return (
    <div className="sv-page sv-aurora relative flex flex-col overflow-x-hidden transition-colors duration-500">

      {/* ── Unified Tactical Navigation Header ── */}
      <SystemHeader title="Challan Terminal" showBack={false} />

      <div className="lg:hidden relative z-[100]">
        <TopSearch isMapPage={false} forceShow={true} showBack={false} />
      </div>

      <main className="flex-1 w-full max-w-7xl mx-auto pt-28 lg:pt-24 pb-44 px-5 sm:px-12 flex flex-col lg:grid lg:grid-cols-[1.2fr,2fr] lg:gap-14 lg:items-start transition-all duration-500">

        {/* ── Left Column: Dynamic Summary & Real-time Quote ── */}
        <aside className="lg:sticky lg:top-28 flex flex-col gap-8 order-2 lg:order-1 mt-10 lg:mt-0">
          <section className="flex flex-col gap-2">
            <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-brand-light/10 border border-brand-light/20 w-fit">
              <span className="w-1.5 h-1.5 rounded-full bg-brand-light animate-pulse"></span>
              <span className="text-[10px] font-semibold text-brand dark:text-brand-light uppercase tracking-[0.1em] font-space leading-none">{t('challan.calculator_active', 'Terminal Active')}</span>
            </div>
            <h1 className="text-3xl font-black tracking-tight text-text-1 uppercase font-space leading-tight">
              {t('challan.title', 'Estimation Terminal')}
            </h1>
          </section>

          {/* ── Dynamic Left-side summary card ── */}
          <section
            ref={resultCardRef}
            className="scan-line-overlay relative p-8 rounded-[2.5rem] bg-white dark:bg-white/5 border border-border shadow-2xl shadow-surface-3/50 dark:shadow-none overflow-hidden group"
          >
            <div className="absolute -bottom-20 -right-20 w-40 h-40 bg-brand-light/10 blur-[80px] rounded-full group-hover:scale-150 transition-transform duration-700" />

            <div className="relative z-10 flex flex-col gap-6">

              {/* Dynamic rendering based on activeTab */}
              {activeTab === 'calculator' && (
                <>
                  <div className="flex flex-col gap-1">
                    <p className="text-[10px] font-semibold text-text-3 uppercase tracking-[0.1em] font-space">{t('challan.total_liability', 'Total Liability')}</p>
                    <h2
                      ref={fineRef}
                      className={`text-5xl sm:text-7xl font-black text-brand dark:text-brand-light tracking-tighter ${isLoading ? 'opacity-50 blur-sm transition-all' : ''}`}
                    >
                      {t('challan.rupees_symbol', 'Rs. ')}{finalFine.toLocaleString('en-IN')}
                    </h2>
                  </div>

                  <div className="flex flex-col gap-3">
                    <div className="flex items-center gap-2 p-3 rounded-xl bg-surface-2 border border-border">
                       <Scale size={16} className="text-brand-light" />
                       <div className="flex flex-col">
                         <span className="text-[11px] font-semibold text-text-1 tracking-tight leading-none uppercase">{activeViolation.mva}</span>
                         <span className="text-[9px] font-bold text-text-3 uppercase tracking-widest mt-1">{isRepeat ? 'Repeat Offence (2x)' : 'First Occurrence'}</span>
                       </div>
                    </div>

                    {activeViolation.danger && (
                      <div
                        ref={dangerRef}
                        className="flex items-center gap-2 px-4 py-2 rounded-lg bg-red-500/10 border border-red-500/20"
                      >
                        <AlertTriangle size={12} className="text-red-500" />
                        <span className="text-[10px] font-semibold text-red-600 dark:text-red-400 uppercase tracking-wider">{activeViolation.danger}</span>
                      </div>
                    )}
                  </div>

                  <div className="relative">
                    <button
                      onClick={() => {
                        setShowDetailToast(true);
                        setTimeout(() => setShowDetailToast(false), 3000);
                      }}
                      className="w-full h-16 bg-brand dark:bg-brand-light rounded-lg flex items-center justify-center gap-3 shadow-xl hover:scale-[1.02] active:scale-95 transition-all group/btn"
                    >
                       <span className="text-white dark:text-text-1 font-black text-sm tracking-[0.1em] uppercase font-space">{t('challan.detailed_report', 'DETAILED REPORT')}</span>
                       <ArrowRight size={18} className="text-white dark:text-text-1 group-hover/btn:translate-x-1 transition-transform" />
                    </button>
                    <div
                      ref={toastRef}
                      style={{ opacity: 0 }}
                      className="absolute -top-12 left-1/2 -translate-x-1/2 px-4 py-2 bg-surface-3 text-text-1 text-[10px] uppercase tracking-widest font-bold rounded-full shadow-xl whitespace-nowrap"
                    >
                      {t('challan.detailed_report_offline', 'Detailed report currently offline')}
                    </div>
                  </div>
                </>
              )}

              {activeTab === 'garage' && (
                <>
                  <div className="flex flex-col gap-1">
                    <p className="text-[10px] font-semibold text-text-3 uppercase tracking-[0.1em] font-space">{t('challan.garage_inventory', 'Garage Inventory')}</p>
                    <h2 className="text-4xl sm:text-5xl font-black text-brand dark:text-brand-light tracking-tighter">
                      {t('challan.vehicle_count', '{{count}} Vehicles', { count: garageVehicles.length })}
                    </h2>
                  </div>

                  <div className="flex flex-col gap-3">
                    <div className="flex items-center gap-2 p-3 rounded-xl bg-surface-2 border border-border">
                       <ShieldCheck size={18} className="text-emerald-500" />
                       <div className="flex flex-col">
                         <span className="text-[11px] font-semibold text-text-1 tracking-tight leading-none uppercase">{t('challan.parivahan_synced', 'PARIVAHAN SYNCED')}</span>
                         <span className="text-[9px] font-bold text-text-3 uppercase tracking-widest mt-1">
                           {t('challan.last_synced', 'Last synced: {{time}}', { time: lastSyncedGarage ? new Date(lastSyncedGarage).toLocaleTimeString() : t('challan.not_synced_yet', 'Not Synced Yet') })}
                         </span>
                       </div>
                    </div>
                  </div>

                  <div className="p-4 rounded-xl bg-surface-2 border border-border">
                     <p className="text-[9px] font-semibold text-text-3 uppercase tracking-widest mb-1">{t('challan.rto_status', 'RTO Registry Status')}</p>
                     <p className="text-xs font-semibold text-emerald-500 uppercase flex items-center gap-1.5">
                       <span className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-ping"></span>
                       {t('challan.active_secure', 'ACTIVE SECURE ACCESS')}
                     </p>
                  </div>
                </>
              )}

              {activeTab === 'telemetry' && (
                <>
                  <div className="flex flex-col gap-1">
                    <p className="text-[10px] font-semibold text-text-3 uppercase tracking-[0.1em] font-space">{t('challan.estimated_annual', 'Estimated Annual Fine')}</p>
                    <h2 className="text-4xl sm:text-5xl font-black text-brand dark:text-brand-light tracking-tighter">
                      {riskAnalysis.estimatedLiability !== null ? `Rs. ${riskAnalysis.estimatedLiability.toLocaleString('en-IN')}` : 'Rs. --'}
                    </h2>
                  </div>

                  <div className="flex flex-col gap-3">
                    <div className="flex items-center gap-3 p-3 rounded-xl bg-surface-2 border border-border">
                       <Activity size={18} className={riskAnalysis.riskLevel === 'high' ? 'text-red-500 animate-pulse' : riskAnalysis.riskLevel === 'medium' ? 'text-amber-500' : 'text-emerald-500'} />
                       <div className="flex flex-col">
                         <span className="text-[11px] font-semibold text-text-1 tracking-tight leading-none uppercase">
                           {t('challan.risk_score', 'Risk score: {{score}}/10.0', { score: riskAnalysis.riskScore !== null ? riskAnalysis.riskScore : '--' })}
                         </span>
                         <span className={`text-[9px] font-bold uppercase tracking-widest mt-1 ${riskAnalysis.riskLevel === 'high' ? 'text-red-500' : riskAnalysis.riskLevel === 'medium' ? 'text-amber-500' : 'text-emerald-500'}`}>
                           {t('challan.risk_tier', 'Tier: {{tier}}', { tier: riskAnalysis.riskLevel || t('challan.unknown', 'Unknown') })}
                         </span>
                       </div>
                    </div>
                  </div>

                  <div className="p-4 rounded-xl bg-surface-2 border border-border">
                     <p className="text-[9px] font-semibold text-text-3 uppercase tracking-widest mb-1">{t('challan.liability_forecast', 'Liability Forecast')}</p>
                     <p className="text-xs font-semibold text-text-1">
                       {t('challan.forecast_desc', 'Based on {{violationsCount}} predicted annual violations.', { violationsCount: riskAnalysis.predictedViolationsCount !== null ? riskAnalysis.predictedViolationsCount : '--' })}
                     </p>
                  </div>
                </>
              )}

              {activeTab === 'dispute' && (
                <>
                  <div className="flex flex-col gap-1">
                    <p className="text-[10px] font-semibold text-text-3 uppercase tracking-[0.1em] font-space">{t('challan.dispute_assistant', 'Dispute Assistant')}</p>
                    <h2 className="text-3xl sm:text-4xl font-black text-brand dark:text-brand-light tracking-tighter uppercase break-words">
                      {disputeResponse ? disputeResponse.dispute_ref : t('challan.no_petition', 'No Petition')}
                    </h2>
                  </div>

                  {disputeResponse && (
                    <div className="flex flex-col gap-3">
                      <div className="flex items-center gap-2 p-3 rounded-xl bg-surface-2 border border-border">
                         <Scale size={18} className="text-brand-light" />
                         <div className="flex flex-col">
                           <span className="text-[11px] font-semibold text-text-1 tracking-tight leading-none uppercase">
                             {t('challan.appeal_probability', 'APPEAL SUCCESS PROBABILITY')}
                           </span>
                           <span className="text-[10px] font-black text-emerald-500 uppercase tracking-widest mt-1">
                             {t('challan.confidence', '{{percent}}% CONFIDENCE', { percent: (disputeResponse.confidence_score * 100).toFixed(0) })}
                           </span>
                         </div>
                      </div>
                      <div className="flex flex-wrap gap-2">
                        {disputeResponse.cited_mva_sections.map(section => (
                          <span key={section} className="px-2.5 py-1 bg-brand-light/10 border border-brand-light/20 text-brand-light text-[9px] font-bold rounded-lg uppercase tracking-wider">
                            {section}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  <div className="p-4 rounded-xl bg-surface-2 border border-border">
                     <p className="text-[9px] font-semibold text-text-3 uppercase tracking-widest mb-1">{t('challan.mva_legal_ref', 'MVA Legal Reference')}</p>
                     <p className="text-xs font-semibold text-text-1 uppercase">
                       {t('challan.draft_under_177', 'DRAFT GENERATED UNDER MVA SECTION 177')}
                     </p>
                  </div>
                </>
              )}

            </div>
          </section>

          {/* Quick Meta */}
          <div className="grid grid-cols-2 gap-4">
             <div className="p-4 rounded-xl bg-surface-2 border border-border">
                <p className="text-[9px] font-semibold text-text-3 uppercase tracking-widest mb-1">{t('challan.max_penalty', 'Max Penalty')}</p>
                <p className="text-xs font-semibold text-text-1">{t('challan.rupees_symbol', 'Rs. ')}{activeViolation.max}</p>
             </div>
             <div className="p-4 rounded-xl bg-surface-2 border border-border">
                <p className="text-[9px] font-semibold text-text-3 uppercase tracking-widest mb-1">{t('challan.act_sync', 'Act Sync')}</p>
                <p className="text-xs font-semibold text-brand-light">{t('challan.mva_act_2019', 'MVA_ACT_2019')}</p>
             </div>
          </div>
        </aside>

        {/* ── Right Column: Input Portfolio ("Big & Simple") ── */}
        <div className="flex flex-col gap-6 order-1 lg:order-2">

           {/* ── Sleek segmented control tab bar ── */}
           <div className="p-1.5 rounded-[1.5rem] bg-white dark:bg-white/5 border border-border grid grid-cols-4 gap-1 text-center relative z-10 shadow-lg">
             {[
               { id: 'calculator', label: 'Calc', icon: <Scale size={14} /> },
               { id: 'garage', label: 'Garage', icon: <Car size={14} /> },
               { id: 'telemetry', label: 'Risk', icon: <Sliders size={14} /> },
               { id: 'dispute', label: 'Dispute', icon: <FileText size={14} /> }
             ].map(tObj => (
               <button
                 key={tObj.id}
                 onClick={() => setActiveTab(tObj.id as ActiveTab)}
                 className={`flex flex-col md:flex-row items-center justify-center gap-1.5 py-3.5 rounded-[1.1rem] text-[10px] md:text-xs font-bold uppercase tracking-wider transition-all duration-300 ${
                   activeTab === tObj.id
                     ? 'bg-brand dark:bg-brand-light text-white dark:text-text-1 shadow-md scale-[1.02] ring-2 ring-brand-light/20'
                     : 'text-text-3 hover:text-text-1 hover:bg-surface-2/40'
                 }`}
               >
                 {tObj.icon}
                 <span>
                    {tObj.id === 'calculator'
                      ? t('challan.tab_calc', 'Calc')
                      : tObj.id === 'garage'
                        ? t('challan.tab_garage', 'Garage')
                        : tObj.id === 'telemetry'
                          ? t('challan.tab_risk', 'Risk')
                          : t('challan.tab_dispute', 'Dispute')}
                 </span>
               </button>
             ))}
           </div>

           {/* ── Interactive Tab Content Container ── */}
           <div ref={tabContentRef} className="flex flex-col gap-10 min-h-[400px]">

             {/* ════════════════════════════════════════════════════════════
                 TAB 1: CALCULATOR (Original Form)
                 ════════════════════════════════════════════════════════════ */}
             {activeTab === 'calculator' && (
               <div className="flex flex-col gap-10 sv-swipe-area" onTouchStart={swipeStart} onTouchEnd={swipeEnd}>
                  {/* Swipe indicator */}
                  <div className="flex justify-center gap-1.5 pb-2 lg:hidden">
                    {swipeSections.map((_, i) => (
                      <div key={i} className={`h-0.5 rounded-full transition-all duration-300 ${i === swipeSection ? 'w-6 bg-brand-light' : 'w-2 bg-border'}`} />
                    ))}
                    <span className="text-xs font-semibold text-text-3 uppercase tracking-widest ml-2 self-center">{t('challan.swipe_indicator', 'Swipe ↔')}</span>
                  </div>

                  {/* Section 1: Violation */}
                  <section ref={violationRef} className="flex flex-col gap-6">
                     <div className="flex items-center justify-between">
                       <h3 className="text-xs font-semibold uppercase tracking-[0.1em] text-text-3 font-space flex items-center gap-2">
                         <Activity size={14} className="text-brand-light" />
                         01. Violation Protocol
                       </h3>
                       <div className="px-3 py-1 rounded-full bg-brand dark:bg-brand-light text-white dark:text-text-1 text-[9px] font-semibold uppercase tracking-widest">
                         {jurisdiction.split(' ')[0]}
                       </div>
                     </div>

                     <div className="relative group">
                       <select
                         aria-label="Select violation type"
                         value={violationId}
                         onChange={(e) => setChallanState({ violation: e.target.value })}
                         className="w-full bg-transparent border-2 border-border rounded-xl p-6 text-lg font-black text-text-1 appearance-none focus:border-brand-light transition-all outline-none cursor-pointer"
                       >
                         {violationOptions.map(v => (
                           <option key={v.id} value={v.id} className="bg-white dark:bg-bg">{v.label}</option>
                         ))}
                       </select>
                       <div className="absolute right-6 top-1/2 -translate-y-1/2 pointer-events-none text-text-3">
                         <ArrowRight size={24} className="rotate-90" />
                       </div>
                     </div>
                  </section>

                  {/* Section 2: Vehicle Selection */}
                  <section ref={vehicleSectionRef} className="flex flex-col gap-6">
                    <h3 className="text-xs font-semibold uppercase tracking-[0.1em] text-text-3 font-space flex items-center gap-2">
                      <Car size={14} className="text-brand-light" />
                      02. Vehicle Identification
                    </h3>

                    <div ref={vehicleGridRef} className="grid grid-cols-2 sm:grid-cols-4 gap-4 sv-stagger">
                       {VEHICLE_CLASSES.map(cls => (
                         <button
                           key={cls.id}
                           onClick={() => setChallanState({ vehicle: cls.id })}
                           className={`sv-card-premium flex flex-col items-center justify-center gap-4 p-6 rounded-[2rem] border-2 transition-all duration-300 active:scale-95 ${
                             vehicleId === cls.id
                              ? 'bg-brand-light border-brand-light/30 text-text-1 shadow-xl shadow-brand-light/20 ring-2 ring-brand-light/20'
                              : 'bg-white dark:bg-white/5 border-border text-text-3 hover:border-text-3 dark:hover:border-white/10 hover:shadow-md'
                           }`}
                         >
                           <div className={`p-4 rounded-lg ${vehicleId === cls.id ? 'bg-white/30' : 'bg-surface-2'}`}>
                             {cls.icon}
                           </div>
                           <div className="flex flex-col items-center">
                              <span className="text-xs font-semibold uppercase tracking-widest text-inherit">
                                {cls.id === '2W' ? t('challan.two_wheeler', '2-Wheeler') : cls.id === '4W' ? t('challan.car_lmv', 'Car/LMV') : cls.id === 'HTV' ? t('challan.truck', 'Truck') : t('challan.bus_comm', 'Bus/COMM')}
                              </span>
                              <span className="text-[8px] font-bold uppercase mt-1 opacity-60 text-inherit">
                                {cls.id === 'HTV' ? t('challan.heavy', 'Heavy') : cls.id === '2W' ? t('challan.light', 'Light') : t('challan.standard', 'Standard')}
                              </span>
                           </div>
                         </button>
                       ))}
                    </div>
                  </section>

                  {/* Section 3: Parameters & Jurisdiction */}
                  <section ref={paramsRef} className="grid grid-cols-1 md:grid-cols-2 gap-8">
                    <div className="flex flex-col gap-4">
                      <h3 className="text-xs font-semibold uppercase tracking-[0.1em] text-text-3 font-space">{t('challan.jurisdiction', '03. Jurisdiction')}</h3>
                      <div className="relative">
                        <select
                          aria-label="Select jurisdiction state"
                          value={jurisdiction}
                          onChange={(e) => setChallanState({ jurisdiction: e.target.value })}
                          className="w-full bg-transparent border-2 border-border rounded-lg py-4 px-5 text-sm font-bold text-text-1 appearance-none focus:border-brand-light transition-all outline-none cursor-pointer"
                        >
                          {stateOptions.map(s => (
                            <option key={s} value={s} className="bg-white dark:bg-bg">{s}</option>
                          ))}
                        </select>
                        <MapPin size={16} className="absolute right-5 top-1/2 -translate-y-1/2 text-text-3 pointer-events-none" />
                      </div>
                    </div>

                    <div className="flex flex-col gap-4">
                      <h3 className="text-xs font-semibold uppercase tracking-[0.1em] text-text-3 font-space">{t('challan.history', '04. History')}</h3>
                      <button
                        onClick={() => setChallanState({ isRepeat: !isRepeat })}
                        className={`w-full h-[58px] rounded-lg border-2 flex items-center justify-between px-6 transition-all ${
                          isRepeat
                          ? 'bg-red-500/10 border-red-500/20 text-red-600'
                          : 'bg-white dark:bg-white/5 border-border text-text-3'
                        }`}
                      >
                        <span className="text-[10px] font-semibold uppercase tracking-widest">{t('challan.repeat_offender', 'Repeat Offender?')}</span>
                        <div className={`w-10 h-5 rounded-full relative transition-colors ${isRepeat ? 'bg-red-500' : 'bg-surface-3'}`}>
                          <div
                            ref={toggleRef}
                            className="absolute top-1 w-3 h-3 rounded-full bg-white shadow-sm"
                            style={{ transform: `translateX(${isRepeat ? 22 : 2}px)` }}
                          />
                        </div>
                      </button>
                    </div>
                  </section>

                  {/* AI Insight Footer */}
                  <div ref={insightRef} className="sv-glass p-6 rounded-[2rem] bg-gradient-to-br from-brand-light/10 to-transparent border border-brand-light/20 flex gap-4">
                    <div className="w-10 h-10 rounded-xl bg-brand-light/20 flex items-center justify-center flex-shrink-0">
                      <Zap size={20} className="text-brand-light" />
                    </div>
                    <div className="flex flex-col gap-1">
                      <p className="text-[10px] font-semibold text-brand-light uppercase tracking-widest">{t('challan.ai_tactical_insight', 'AI Tactical Insight')}</p>
                      <p className="text-[11px] font-medium text-text-2 leading-relaxed">
                        {result?.description || `Based on recent MVA amendments, high-risk offences like DUI (${activeViolation.mva}) have immediate license disqualification protocols active in ${jurisdiction.split(' ')[0]}.`}
                      </p>
                    </div>
                  </div>
               </div>
             )}

             {/* ════════════════════════════════════════════════════════════
                 TAB 2: GARAGE (RTO parivahan Sync)
                 ════════════════════════════════════════════════════════════ */}
             {activeTab === 'garage' && (
               <div className="flex flex-col gap-8">
                 <section className="flex flex-col gap-6">
                   <h3 className="text-xs font-semibold uppercase tracking-[0.1em] text-text-3 font-space flex items-center gap-2">
                     <RefreshCw size={14} className="text-brand-light animate-spin-slow" />
                     {t('challan.parivahan_portal', 'Parivahan Transport Sync Portal')}
                   </h3>

                   <form onSubmit={handleSync} className="flex flex-col md:flex-row gap-4">
                     <div className="flex-1 relative">
                       <input
                         aria-label="Enter vehicle registration number"
                         type="text"
                         value={vehicleNo}
                         onChange={(e) => setVehicleNo(e.target.value.toUpperCase())}
                         placeholder={t('challan.vehicle_no_placeholder', 'e.g. TN-01-AB-1234')}
                         className="w-full bg-transparent border-2 border-border rounded-xl py-4 px-6 text-sm font-bold text-text-1 focus:border-brand-light transition-all outline-none"
                         required
                       />
                       <span className="absolute right-5 top-1/2 -translate-y-1/2 text-text-3 text-[10px] font-bold font-space uppercase">{t('challan.rto_reg', 'RTO REG')}</span>
                     </div>

                     <button
                       type="submit"
                       disabled={syncing}
                       className="h-14 px-8 bg-brand dark:bg-brand-light text-white dark:text-text-1 font-bold text-xs uppercase tracking-wider rounded-xl shadow-lg flex items-center justify-center gap-2.5 hover:scale-[1.02] active:scale-95 disabled:opacity-50 transition-all font-space"
                     >
                       {syncing ? <RefreshCw size={14} className="animate-spin" /> : <Plus size={14} />}
                       <span>{syncing ? t('challan.syncing_car', 'SYNCING CAR...') : t('challan.sync_garage_vehicle', 'SYNC GARAGE VEHICLE')}</span>
                     </button>
                   </form>

                   {syncError && (
                     <div className="px-4 py-3 bg-red-500/10 border border-red-500/20 text-red-500 text-xs rounded-xl flex items-center gap-2">
                       <AlertOctagon size={14} />
                       <span>{syncError}</span>
                     </div>
                   )}
                 </section>

                 <section className="flex flex-col gap-6">
                   <h4 className="text-xs font-semibold uppercase tracking-widest text-text-3 font-space">
                     {t('challan.my_citizen_garage', 'My Citizen Garage ({{count}})', { count: garageVehicles.length })}
                   </h4>

                   {garageVehicles.length === 0 ? (
                     <div className="p-12 text-center border-2 border-dashed border-border rounded-[2rem] flex flex-col items-center gap-4">
                       <Car size={40} className="text-text-3 opacity-30" />
                       <div className="flex flex-col">
                         <p className="text-sm font-bold text-text-1">{t('challan.no_vehicles', 'No Vehicles Configured')}</p>
                         <p className="text-[10px] font-medium text-text-3 uppercase tracking-widest mt-1">
                           {t('challan.no_vehicles_desc', 'Enter your registration details above to sync Parivahan registers.')}
                         </p>
                       </div>
                     </div>
                   ) : (
                     <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                       {garageVehicles.map((vehicle: VehicleGarageItem) => (
                         <div
                           key={vehicle.id}
                           className="sv-glass p-6 rounded-[2.5rem] bg-gradient-to-br from-white/10 to-transparent border border-border shadow-xl flex flex-col gap-4 relative overflow-hidden group"
                         >
                           <div className="absolute top-0 right-0 w-24 h-24 bg-brand-light/5 blur-xl rounded-full" />

                           <div className="flex justify-between items-start">
                             <div className="flex items-center gap-3">
                               <div className="w-10 h-10 rounded-xl bg-brand-light/20 flex items-center justify-center text-brand-light">
                                 {vehicle.vehicle_make === 'TATA' ? <Car size={20} /> : <Bike size={20} />}
                               </div>
                               <div className="flex flex-col">
                                 <h5 className="text-sm font-black text-text-1">{vehicle.vehicle_make} {vehicle.vehicle_model}</h5>
                                 <span className="text-[10px] font-bold text-text-3 font-space">{vehicle.vehicle_number}</span>
                               </div>
                             </div>

                             <span className="px-2 py-0.5 bg-emerald-500/10 border border-emerald-500/20 text-emerald-500 text-[8px] font-bold rounded uppercase tracking-wider">
                               {vehicle.rc_status}
                             </span>
                           </div>

                           <div className="grid grid-cols-2 gap-3 pt-2 border-t border-border/40">
                             <div className="flex flex-col">
                               <span className="text-[8px] font-semibold text-text-3 uppercase tracking-widest">{t('challan.owner_record', 'Owner Record')}</span>
                               <span className="text-[10px] font-bold text-text-1 mt-0.5">{vehicle.owner_name}</span>
                             </div>
                             <div className="flex flex-col">
                               <span className="text-[8px] font-semibold text-text-3 uppercase tracking-widest">{t('challan.insurance_exp', 'Insurance Exp.')}</span>
                               <span className="text-[10px] font-bold text-text-1 mt-0.5">
                                 {vehicle.insurance_expiry ? new Date(vehicle.insurance_expiry).toLocaleDateString() : 'N/A'}
                               </span>
                             </div>
                           </div>

                           <div className="flex items-center gap-1.5 p-2 bg-emerald-500/5 rounded-lg border border-emerald-500/10">
                             <ShieldCheck size={12} className="text-emerald-500" />
                             <span className="text-[9px] font-bold text-emerald-600 dark:text-emerald-400 uppercase tracking-wide">
                               {t('challan.puc_valid', 'PUC Pollution Certificate Valid (Exp: {{expiry}})', { expiry: vehicle.puc_expiry ? new Date(vehicle.puc_expiry).toLocaleDateString() : 'N/A' })}
                             </span>
                           </div>
                         </div>
                       ))}
                     </div>
                   )}
                 </section>
               </div>
             )}

             {/* ════════════════════════════════════════════════════════════
                 TAB 3: TELEMETRY (Risk Fine Predictor)
                 ════════════════════════════════════════════════════════════ */}
             {activeTab === 'telemetry' && (
               <div className="flex flex-col gap-8">
                 <section className="flex flex-col gap-6">
                   <h3 className="text-xs font-semibold uppercase tracking-[0.1em] text-text-3 font-space flex items-center gap-2">
                     <Sliders size={14} className="text-brand-light" />
                     {t('challan.telemetry_title', 'Driving Telemetry Log Integration')}
                   </h3>

                   <div className="grid grid-cols-1 md:grid-cols-2 gap-6">

                     {/* Speeding Events Slider */}
                     <div className="flex flex-col gap-2 p-5 rounded-2xl bg-surface-2 border border-border">
                       <div className="flex justify-between items-center">
                         <span className="text-[10px] font-black uppercase text-text-1">{t('challan.speeding_events', 'Speeding Events')}</span>
                         <span className="text-xs font-black text-brand-light">{t('challan.per_month', '{{count}} / Month', { count: speedingEvents })}</span>
                       </div>
                       <input
                         aria-label="Speeding Events"
                         type="range"
                         min="0"
                         max="20"
                         value={speedingEvents}
                         onChange={(e) => setSpeedingEvents(Number(e.target.value))}
                         className="w-full accent-brand-light bg-border h-1 rounded-lg outline-none cursor-pointer"
                       />
                       <span className="text-[9px] font-medium text-text-3">{t('challan.speeding_desc', 'Counts high-severity speeding over guidelines.')}</span>
                     </div>

                     {/* Harsh Braking Slider */}
                     <div className="flex flex-col gap-2 p-5 rounded-2xl bg-surface-2 border border-border">
                       <div className="flex justify-between items-center">
                         <span className="text-[10px] font-black uppercase text-text-1">{t('challan.harsh_braking', 'Harsh Braking')}</span>
                         <span className="text-xs font-black text-brand-light">{t('challan.per_month', '{{count}} / Month', { count: harshBraking })}</span>
                       </div>
                       <input
                         aria-label="Harsh Braking Events"
                         type="range"
                         min="0"
                         max="20"
                         value={harshBraking}
                         onChange={(e) => setHarshBraking(Number(e.target.value))}
                         className="w-full accent-brand-light bg-border h-1 rounded-lg outline-none cursor-pointer"
                       />
                       <span className="text-[9px] font-medium text-text-3">{t('challan.braking_desc', 'Detects sudden decel forces on gyro sensors.')}</span>
                     </div>

                     {/* Night Driving Minutes */}
                     <div className="flex flex-col gap-2 p-5 rounded-2xl bg-surface-2 border border-border">
                       <div className="flex justify-between items-center">
                         <span className="text-[10px] font-black uppercase text-text-1">{t('challan.night_driving', 'Night Driving Time')}</span>
                         <span className="text-xs font-black text-brand-light">{t('challan.minutes_count', '{{count}} Mins', { count: nightDriving })}</span>
                       </div>
                       <input
                         aria-label="Night Driving Minutes"
                         type="range"
                         min="0"
                         max="480"
                         value={nightDriving}
                         onChange={(e) => setNightDriving(Number(e.target.value))}
                         className="w-full accent-brand-light bg-border h-1 rounded-lg outline-none cursor-pointer"
                       />
                       <span className="text-[9px] font-medium text-text-3">{t('challan.night_driving_desc', 'Drives between 11PM to 5AM increases risk.')}</span>
                     </div>

                     {/* Total Kilometers */}
                     <div className="flex flex-col gap-2 p-5 rounded-2xl bg-surface-2 border border-border">
                       <div className="flex justify-between items-center">
                         <span className="text-[10px] font-black uppercase text-text-1">{t('challan.monthly_distance', 'Monthly Distance')}</span>
                         <span className="text-xs font-black text-brand-light">{totalKm} KM</span>
                       </div>
                       <input
                         aria-label="Monthly Distance"
                         type="range"
                         min="100"
                         max="5000"
                         value={totalKm}
                         onChange={(e) => setTotalKm(Number(e.target.value))}
                         className="w-full accent-brand-light bg-border h-1 rounded-lg outline-none cursor-pointer"
                       />
                       <span className="text-[9px] font-medium text-text-3">{t('challan.distance_desc', 'Total mileage calculated.')}</span>
                     </div>

                   </div>

                   <button
                     onClick={handlePredict}
                     disabled={predicting}
                     className="w-full h-14 bg-brand dark:bg-brand-light text-white dark:text-text-1 font-bold text-xs uppercase tracking-wider rounded-xl shadow-lg flex items-center justify-center gap-2.5 hover:scale-[1.02] active:scale-95 disabled:opacity-50 transition-all font-space"
                   >
                     {predicting ? <RefreshCw size={14} className="animate-spin" /> : <Activity size={14} />}
                     <span>{predicting ? t('challan.forecasting_risk', 'FORECASTING RISK...') : t('challan.run_predictor', 'RUN FINE LIABILITY PREDICTOR')}</span>
                   </button>

                   {predictError && (
                     <div className="px-4 py-3 bg-red-500/10 border border-red-500/20 text-red-500 text-xs rounded-xl flex items-center gap-2">
                       <AlertOctagon size={14} />
                       <span>{predictError}</span>
                     </div>
                   )}
                 </section>

                 {/* Recommendations Checklist */}
                 {riskAnalysis.recommendations.length > 0 && (
                   <section className="flex flex-col gap-4">
                     <h4 className="text-xs font-semibold uppercase tracking-widest text-text-3 font-space">
                       {t('challan.recommendations_title', 'SafeDriving Tactical Recommendations')}
                     </h4>

                     <div className="flex flex-col gap-3">
                       {riskAnalysis.recommendations.map((rec: string, index: number) => (
                         <div key={index} className="p-4 rounded-xl bg-surface-2 border border-border flex gap-3 items-start">
                           <div className="w-5 h-5 rounded-md bg-brand-light/20 flex items-center justify-center flex-shrink-0 text-brand-light mt-0.5">
                             <CheckCircle size={12} />
                           </div>
                           <span className="text-xs text-text-2 font-medium leading-relaxed">{rec}</span>
                         </div>
                       ))}
                     </div>
                   </section>
                 )}
               </div>
             )}

             {/* ════════════════════════════════════════════════════════════
                 TAB 4: DISPUTE (AI Appeal drafting)
                 ════════════════════════════════════════════════════════════ */}
             {activeTab === 'dispute' && (
               <div className="flex flex-col gap-8">
                 <section className="flex flex-col gap-6">
                   <h3 className="text-xs font-semibold uppercase tracking-[0.1em] text-text-3 font-space flex items-center gap-2">
                     <Scale size={14} className="text-brand-light" />
                     {t('challan.dispute_title', 'e-Challan Dispute drafting Assistant')}
                   </h3>

                   <form onSubmit={handleDraft} className="grid grid-cols-1 md:grid-cols-2 gap-6">

                     <div className="flex flex-col gap-2">
                       <label className="text-[10px] font-bold text-text-3 uppercase tracking-widest">{t('challan.challan_ref', 'Challan Reference Number')}</label>
                       <input
                         type="text"
                         aria-label="Challan Reference Number"
                         value={challanRefNo}
                         onChange={(e) => setChallanRefNo(e.target.value.toUpperCase())}
                         placeholder="CH-2026-XXXX"
                         className="w-full bg-transparent border-2 border-border rounded-xl py-3.5 px-4 text-sm font-bold text-text-1 focus:border-brand-light transition-all outline-none"
                         required
                       />
                     </div>

                     <div className="flex flex-col gap-2">
                       <label className="text-[10px] font-bold text-text-3 uppercase tracking-widest">{t('challan.fine_amount', 'Fine Amount (Rs)')}</label>
                       <input
                         type="number"
                         aria-label="Fine Amount"
                         value={disputeFine}
                         onChange={(e) => setDisputeFine(Number(e.target.value))}
                         className="w-full bg-transparent border-2 border-border rounded-xl py-3.5 px-4 text-sm font-bold text-text-1 focus:border-brand-light transition-all outline-none"
                         required
                       />
                     </div>

                     <div className="flex flex-col gap-2">
                       <label className="text-[10px] font-bold text-text-3 uppercase tracking-widest">{t('challan.violation_code', 'Infraction Violation Code')}</label>
                       <select
                         aria-label="Select Violation Code for Dispute"
                         value={disputeCode}
                         onChange={(e) => setDisputeCode(e.target.value)}
                         className="w-full bg-transparent border-2 border-border rounded-xl py-3.5 px-4 text-sm font-bold text-text-1 focus:border-brand-light transition-all outline-none cursor-pointer"
                       >
                         <option value="183" className="bg-white dark:bg-bg">{t('challan.dispute_violation_183', 'Speeding (>20km/h Limit) - Sec 183')}</option>
                         <option value="185" className="bg-white dark:bg-bg">{t('challan.dispute_violation_185', 'Drunk Driving - Sec 185')}</option>
                         <option value="177" className="bg-white dark:bg-bg">{t('challan.dispute_violation_177', 'Disobedience / Red Light - Sec 177')}</option>
                       </select>
                     </div>

                     <div className="flex flex-col gap-2 md:col-span-2">
                       <label className="text-[10px] font-bold text-text-3 uppercase tracking-widest">{t('challan.mitigating_factors', 'Mitigating Circumstances')}</label>
                       <textarea
                         aria-label="Mitigating Circumstances Text"
                         rows={3}
                         value={mitigatingFactors}
                         onChange={(e) => setMitigatingFactors(e.target.value)}
                         placeholder={t('challan.mitigating_placeholder', 'Explain clearly what happened (e.g. speed board covered by branches, emergency vehicle passage...)')}
                         className="w-full bg-transparent border-2 border-border rounded-xl py-3.5 px-4 text-sm font-medium text-text-1 focus:border-brand-light transition-all outline-none leading-relaxed"
                         required
                       />
                     </div>

                     <button
                       type="submit"
                       disabled={draftingDispute}
                       className="md:col-span-2 h-14 bg-brand dark:bg-brand-light text-white dark:text-text-1 font-bold text-xs uppercase tracking-wider rounded-xl shadow-lg flex items-center justify-center gap-2.5 hover:scale-[1.02] active:scale-95 disabled:opacity-50 transition-all font-space"
                     >
                       {draftingDispute ? <RefreshCw size={14} className="animate-spin" /> : <FileText size={14} />}
                       <span>{draftingDispute ? t('challan.drafting_petition', 'DRAFTING PETITION...') : t('challan.generate_appeal', 'GENERATE FORMAL COURT APPEAL')}</span>
                     </button>

                   </form>

                   {disputeError && (
                     <div className="px-4 py-3 bg-red-500/10 border border-red-500/20 text-red-500 text-xs rounded-xl flex items-center gap-2">
                       <AlertOctagon size={14} />
                       <span>{disputeError}</span>
                     </div>
                   )}
                 </section>

                 {/* Appeal scroll preview */}
                 {disputeResponse && (
                   <section className="flex flex-col gap-4">
                     <div className="flex justify-between items-center">
                       <h4 className="text-xs font-semibold uppercase tracking-widest text-text-3 font-space">
                         {t('challan.draft_scroll', 'Draft Representation Scroll')}
                       </h4>
                       <div className="flex gap-2">
                         <button
                           onClick={handleEmailAppeal}
                           className="text-[10px] font-bold font-space uppercase tracking-widest px-3 py-1.5 rounded-lg bg-surface-2 border border-border text-brand-light flex items-center gap-1.5 hover:bg-surface-3 transition-colors"
                         >
                           <Mail size={12} />
                           {t('challan.email_appeal', 'EMAIL APPEAL')}
                         </button>
                         <button
                           onClick={handleCopy}
                           className="text-[10px] font-bold font-space uppercase tracking-widest px-3 py-1.5 rounded-lg bg-surface-2 border border-border text-brand-light flex items-center gap-1.5 hover:bg-surface-3 transition-colors"
                         >
                           {copied ? <Check size={12} className="text-emerald-500" /> : <Clipboard size={12} />}
                           {copied ? t('challan.copied', 'COPIED') : t('challan.copy_scroll', 'COPY SCROLL')}
                         </button>
                       </div>
                     </div>

                     <div className="p-8 rounded-[2rem] border border-border bg-amber-500/5 dark:bg-yellow-500/5 relative overflow-hidden font-serif text-sm leading-relaxed text-text-1 max-h-[400px] overflow-y-auto whitespace-pre-line shadow-inner">
                       {disputeResponse.appeal_letter}
                     </div>

                     <div className="flex flex-col gap-3">
                       <h5 className="text-[10px] font-bold text-text-3 uppercase tracking-widest font-space">{t('challan.filing_instructions', 'Filing Instructions')}</h5>
                       {disputeResponse.instructions.map((inst, index) => (
                         <div key={index} className="flex gap-2.5 items-start text-xs text-text-2 font-medium">
                           <span className="w-5 h-5 rounded-full bg-brand-light/10 border border-brand-light/20 text-brand-light text-[10px] font-bold flex items-center justify-center flex-shrink-0">{index + 1}</span>
                           <span className="leading-relaxed mt-0.5">{inst}</span>
                         </div>
                       ))}
                     </div>
                   </section>
                 )}
               </div>
             )}

           </div>

           {/* Legal Disclaimer Box */}
           <div className="p-5 rounded-2xl bg-surface-2 border border-border flex flex-col gap-2 opacity-80">
             <p className="text-[9px] font-bold text-text-3 uppercase tracking-widest flex items-center gap-1.5">
               <Scale size={10} className="text-text-3" />
               {t('challan.disclaimer_title', 'Legal Disclaimer & Caveats')}
             </p>
             <p className="text-[10px] font-medium text-text-3 leading-relaxed">
               {t('challan.disclaimer_desc', 'This is a citizens\' estimation terminal. Fine amounts are estimates based on the Motor Vehicles (Amendment) Act 2019 and state-level overrides. This tool does not provide binding legal advice, official adjudications, or formal citation resolutions. Please consult legal counsel or refer to official government traffic department notifications for absolute verification.')}
             </p>
           </div>

        </div>
      </main>
    </div>
  );
}
