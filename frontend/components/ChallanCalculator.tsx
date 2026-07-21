'use client';

// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team


import React, { useState, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { useGSAP } from '@gsap/react';


import { calculateChallan, type ChallanResult } from '@/lib/api';
import { logClientError } from '@/lib/client-logger';


import { track } from '@/lib/analytics';
import { haptics } from '@/lib/haptics';
import { gsap } from '@/lib/gsap';
import { formatCurrency } from '@/lib/intl-formatters';

/**
 * ChallanCalculator — High-Fidelity Fine Specialist
 * Implements Stitch Design: `6304aa246be8445781a95e263d919f85`
 * Features: Visual violation selector, state-specific fine lookup, and premium result cards.
 */
const ChallanCalculator: React.FC = () => {
 const { t } = useTranslation();
 const [violationCode, setViolationCode] = useState('194D');
 const [vehicleClass, setVehicleClass] = useState('2W');
 const [stateCode, setStateCode] = useState('TN');
 const [isRepeat, setIsRepeat] = useState(false);
 const [result, setResult] = useState<(ChallanResult & { source: string }) | null>(null);
 const [error, setError] = useState<string | null>(null);
 const [loading, setLoading] = useState(false);

  const violationRef = useRef<HTMLDivElement>(null);
  const configRef = useRef<HTMLDivElement>(null);
  const resultRef = useRef<HTMLDivElement>(null);

  useGSAP(() => {
    gsap.fromTo([violationRef.current, configRef.current],
      { opacity: 0, y: 15 },
      { opacity: 1, y: 0, duration: 0.5, stagger: 0.15, ease: 'power2.out' }
    );
  }, { dependencies: [] });

  useGSAP(() => {
    if (result && resultRef.current) {
      gsap.fromTo(resultRef.current,
        { opacity: 0, y: 20, scale: 0.95 },
        { opacity: 1, y: 0, scale: 1, duration: 0.4, ease: 'back.out(1.5)' }
      );
    }
  }, { scope: resultRef, dependencies: [result] });

  const VIOLATIONS = [
    { code: '194D', label: t('challan.violation_194D', 'No Seatbelt/Helmet'), icon: '🪖' },
    { code: '183', label: t('challan.violation_183', 'Speeding'), icon: '⚡' },
    { code: '185', label: t('challan.violation_185', 'Drunk Driving'), icon: '🍷' },
    { code: '181', label: t('challan.violation_181', 'License'), icon: '🪪' },
    { code: '179', label: t('challan.violation_179', 'Disobedience'), icon: '🛑' },
  ];
 const STATES = [
 { code: 'AP', label: 'Andhra Pradesh' }, { code: 'AR', label: 'Arunachal Pradesh' },
 { code: 'AS', label: 'Assam' }, { code: 'BR', label: 'Bihar' },
 { code: 'CG', label: 'Chhattisgarh' }, { code: 'GA', label: 'Goa' },
 { code: 'GJ', label: 'Gujarat' }, { code: 'HR', label: 'Haryana' },
 { code: 'HP', label: 'Himachal Pradesh' }, { code: 'JH', label: 'Jharkhand' },
 { code: 'KA', label: 'Karnataka' }, { code: 'KL', label: 'Kerala' },
 { code: 'MP', label: 'Madhya Pradesh' }, { code: 'MH', label: 'Maharashtra' },
 { code: 'MN', label: 'Manipur' }, { code: 'ML', label: 'Meghalaya' },
 { code: 'MZ', label: 'Mizoram' }, { code: 'NL', label: 'Nagaland' },
 { code: 'OD', label: 'Odisha' }, { code: 'PB', label: 'Punjab' },
 { code: 'RJ', label: 'Rajasthan' }, { code: 'SK', label: 'Sikkim' },
 { code: 'TN', label: 'Tamil Nadu' }, { code: 'TS', label: 'Telangana' },
 { code: 'TR', label: 'Tripura' }, { code: 'UP', label: 'Uttar Pradesh' },
 { code: 'UK', label: 'Uttarakhand' }, { code: 'WB', label: 'West Bengal' },
 { code: 'AN', label: 'Andaman & Nicobar' }, { code: 'CH', label: 'Chandigarh' },
 { code: 'DN', label: 'Dadra/Nagar Haveli/Daman/Diu' }, { code: 'DL', label: 'Delhi' },
 { code: 'JK', label: 'Jammu & Kashmir' }, { code: 'LA', label: 'Ladakh' },
 { code: 'LD', label: 'Lakshadweep' }, { code: 'PY', label: 'Puducherry' },
 ];

  const handleCalculate = async () => {
    setLoading(true);
    setResult(null);
    setError(null);

    try {
      const data = await calculateChallan({
        violation_code: violationCode,
        vehicle_class: vehicleClass,
        state_code: stateCode,
        is_repeat: isRepeat
      });
      setResult({ ...data, source: data.source || 'online' });
      track.challanCalculated(
        stateCode,
        data.section,
        data.amount_due,
        isRepeat
      );
    } catch (err) {
      logClientError('Calculation failed:', err);
      setError(t('challan.calculation_failed', 'Unable to calculate this challan right now. Please check your connectivity.'));
    } finally {
      setLoading(false);
    }
  };

 return (
 <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
 
  {/* Violation Selection Grid */}
  <div ref={violationRef} className="space-y-4" role="radiogroup" aria-label="Select Violation Type">
  <div className="text-[10px] font-semibold uppercase tracking-widest text-brand/40 px-2">{t('challan.violation_protocol', '01. Violation Protocol')}</div>
  <div className="grid grid-cols-2 gap-3">
  {VIOLATIONS.map((v) => (
  <button
  key={v.code}
  onClick={() => {
     setViolationCode(v.code);
     haptics.light();
  }}
  role="radio"
  aria-checked={violationCode === v.code}
  aria-label={`Violation: ${v.label}`}
  className={`flex flex-col items-center justify-center p-4 rounded-[1.5rem] border transition-all gap-2 ${
  violationCode === v.code 
  ? 'bg-brand text-bg border-transparent shadow-[0_4px_20px_rgba(26,92,56,0.4)]' 
  : 'bg-surface-1/40 text-brand border-brand/10 hover:bg-brand/5'
  }`}
  >
  <div className="text-xl" aria-hidden="true">{v.icon}</div>
  <div className="text-[9px] font-semibold uppercase tracking-widest text-center">{v.label}</div>
  </button>
  ))}
  </div>
  </div>

 {/* Config Panel */}
 <div ref={configRef} className="bg-surface-1/60 backdrop-blur-3xl p-6 rounded-[2rem] border border-brand/5 space-y-6">
 <div className="grid grid-cols-2 gap-4">
  <div className="space-y-2">
  <label id="vehicle-class-label" className="text-[9px] font-semibold uppercase tracking-widest text-brand/40">{t('challan.vehicle_identification', '02. Vehicle Identification')}</label>
  <select 
  aria-labelledby="vehicle-class-label"
  value={vehicleClass} 
  onChange={(e) => {
     setVehicleClass(e.target.value);
     haptics.light();
  }}
  className="w-full bg-bg/40 border border-brand/10 rounded-xl p-3 text-xs text-text-1 outline-none font-medium"
  >
 <option value="2W">{t('challan.two_wheeler', '2-Wheeler')}</option>
 <option value="LMV">{t('challan.car_lmv', 'Car/LMV')}</option>
 <option value="HMV">{t('challan.truck', 'Truck')}</option>
 </select>
 </div>
  <div className="space-y-2">
  <label id="state-ut-label" className="text-[9px] font-semibold uppercase tracking-widest text-brand/40">{t('challan.jurisdiction', '03. Jurisdiction')}</label>
  <select 
  aria-labelledby="state-ut-label"
  value={stateCode} 
  onChange={(e) => {
     setStateCode(e.target.value);
     haptics.light();
  }}
  className="w-full bg-bg/40 border border-brand/10 rounded-xl p-3 text-xs text-text-1 outline-none font-medium"
  >
 {STATES.map((state) => (
 <option key={state.code} value={state.code}>{state.label}</option>
 ))}
 </select>
 </div>
 </div>

  <button 
  onClick={() => {
     setIsRepeat(!isRepeat);
     haptics.light();
  }}
  aria-pressed={isRepeat}
  className={`w-full py-3 rounded-xl border transition-all flex items-center justify-center gap-3 ${
  isRepeat 
  ? 'bg-emergency/10 border-emergency/40 text-emergency' 
  : 'bg-white/5 border-white/10 text-brand/40'
  }`}
  >
  <div className={`w-3 h-3 rounded-full ${isRepeat ? 'bg-emergency animate-pulse' : 'bg-white/10'}`} aria-hidden="true" />
  <span className="text-[10px] font-semibold uppercase tracking-widest">{t('challan.repeat_offender', 'Repeat Offender?')}</span>
  </button>

 <button 
 onClick={() => {
    handleCalculate();
    haptics.light();
  }}
 disabled={loading}
 className="w-full py-5 bg-brand text-bg rounded-[1.5rem] text-[11px] font-semibold uppercase tracking-widest shadow-2xl hover:scale-[1.02] active:scale-95 transition-all"
 >
 {loading ? t('challan.loading', 'Processing...') : t('challan.title', 'Calculate Penalty')}
 </button>
 </div>

  {/* Result Display */}
  {error && (
  <div role="alert" className="rounded-2xl border border-red-500/20 bg-red-500/10 p-4 text-sm font-semibold text-red-300">
  {error}
  </div>
  )}
  {result && (
 <div
 ref={resultRef}
 className="bg-surface-1 border-2 border-brand/20 p-8 rounded-[2.5rem] shadow-[0_20px_50px_rgba(0,0,0,0.4)] relative overflow-hidden"
 >
 <div className="absolute top-0 right-0 w-32 h-32 bg-emergency/5 blur-[60px] rounded-full" />
 
 <div className="relative z-10">
 <div className="flex justify-between items-start mb-6">
 <div>
 <h4 className="text-[10px] font-semibold uppercase tracking-widest text-emergency mb-1">Section {result.section} CMV Act</h4>
 <p className="text-sm font-bold text-text-1 leading-tight">{result.description}</p>
 </div>
 <div className="bg-brand/10 px-3 py-1 rounded-full border border-brand/20 text-[9px] font-semibold text-brand">
 {result.source.toUpperCase()}
 </div>
 </div>

 <div className="flex items-baseline gap-2">
 <span className="text-4xl font-black text-text-1 tracking-tighter">
   {formatCurrency(result.amount_due)}
 </span>
 {isRepeat && (
 <span className="text-[10px] font-semibold text-emergency uppercase tracking-widest ml-2">{t('challan.repeat_offence', 'Repeat Offence')}</span>
 )}
 </div>

 <div className="mt-8 pt-6 border-t border-white/5 flex gap-4">
 <button className="flex-1 py-3 bg-brand/10 hover:bg-brand/20 rounded-xl text-brand text-[9px] font-semibold uppercase tracking-widest border border-brand/20">
 {t('challan.ai_guidance', 'AI Guidance')}
 </button>
 <button className="flex-1 py-3 bg-brand text-bg rounded-xl text-[9px] font-semibold uppercase tracking-widest">
 {t('profile.save', 'Save')}
 </button>
 </div>
 </div>
 </div>
 )}
 </div>
 );
};

export default ChallanCalculator;