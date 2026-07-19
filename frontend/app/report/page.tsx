// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
import React from 'react';

'use client';

import { useEffect, useMemo, useState, useRef } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { useTranslation } from 'react-i18next';
import {
  AlertTriangle,
  Camera,
  CheckCircle2,
  Loader2,
  MapPin,
  Mic,
  Navigation,
  Phone,
  RefreshCcw,
  Send,
  ShieldAlert,
  Upload,
} from 'lucide-react';
import { validateImageFile, compressImageFile } from '@/lib/validate-upload';
import { usePageEntry } from '@/hooks/usePageEntry';

import TopSearch from '@/components/dashboard/TopSearch';
import { TerminalHeader } from '@/components/ui/TerminalHeader';
import { SurfaceCard } from '@/components/ui/SurfaceCard';
import HazardViewfinder from '@/components/report/HazardViewfinder';
import { ReportProgressBar } from '@/components/report/ReportProgressBar';
import LocationPicker from '@/components/report/LocationPicker';
import {
  type AuthorityPreviewResponse,
  type RoadInfrastructureResponse,
  type RoadReportResponse,
  fetchAuthorityPreview,
  fetchRoadInfrastructure,
  reverseGeocode,
  submitReport,
} from '@/lib/api';
import { useGeolocation } from '@/lib/geolocation';
import {
  formatAccuracyLabel,
  formatLocationLabel,
  formatLocationSubtitle,
  isApproximateLocation,
} from '@/lib/location-utils';
import { useSwipe } from '@/hooks/useSwipe';
import { useSetGpsLocation } from '@/lib/store';
import { track } from '@/lib/analytics';

const ISSUE_OPTIONS_BY_CATEGORY = {
  roads: [
    ['pothole', 'Pothole', 'Surface collapse or broken asphalt'],
    ['crack', 'Road Crack', 'Structural fissures or surface wear'],
    ['waterlogging', 'Waterlogging', 'Flooding, drainage failure, waterlogged lanes'],
    ['debris', 'Road Debris', 'Objects blocking lanes or endangering traffic'],
    ['footpath', 'Footpath', 'Broken pavements or pedestrian path blockages'],
    ['markings', 'Road Markings', 'Faded lanes, zebra crossing wear, missing paint'],
  ],
  traffic: [
    ['signal_outage', 'Signal Outage', 'Traffic light dark, flashing, or broken'],
    ['missing_sign', 'Missing Sign', 'Stop, speed limits, or warning signs missing'],
    ['zebra_crossing', 'Zebra Crossing', 'Dangerous or faded crosswalks needing repair'],
    ['speed_bump', 'Speed Bump', 'Missing warning lines or broken speed calmers'],
    ['encroachment', 'Obstruction', 'Vendors, illegal parking, or structural blocks'],
  ],
  streetlight: [
    ['dark_street', 'Dark Street', 'Entire stretch or segment with dead streetlights'],
    ['bulb_out', 'Bulb Out', 'Single lamp post bulb burned out or dim'],
    ['pole_damage', 'Pole Damage', 'Critically tilted, rusted, or structurally unsafe pole'],
    ['electrical_hazard', 'Electrical Hazard', 'Exposed wires, open junction boxes, spark risk'],
  ],
} as const;

const SEVERITY_OPTIONS = [
  [1, 'Low', 'Monitor only'],
  [2, 'Guarded', 'Needs maintenance soon'],
  [3, 'Serious', 'Affects safe driving now'],
  [4, 'Critical', 'Immediate authority response'],
  [5, 'Extreme', 'High-risk emergency condition'],
] as const;

const severityKeyMap: Record<number, string> = {
  1: 'low',
  2: 'guarded',
  3: 'serious',
  4: 'critical',
  5: 'extreme'
};

function cx(...values: Array<string | false | null | undefined>) {
  return values.filter(Boolean).join(' ');
}

function extractApiError(error: unknown, fallback: string) {
  if (typeof error === 'object' && error !== null) {
    const maybe = error as { response?: { data?: { detail?: string } }; message?: string };
    if (typeof maybe.response?.data?.detail === 'string') return maybe.response.data.detail;
    if (typeof maybe.message === 'string') return maybe.message;
  }
  return fallback;
}

function formatMoney(value: number | null | undefined) {
  if (typeof value !== 'number' || Number.isNaN(value)) return 'Not published';
  return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(value);
}

function normalizeExternalUrl(url: string | null | undefined) {
  if (!url) return null;
  if (/^https?:\/\//i.test(url)) return url;
  return `https://${url}`;
}


export default function ReportPage() {
  const { t } = useTranslation();
  const pageRef = usePageEntry();
  const [mounted, setMounted] = useState(false);
  const [activeCategory, setActiveCategory] = useState<'roads' | 'traffic' | 'streetlight'>('roads');
  const [selectedType, setSelectedType] = useState<string | null>(null);
  const [citizenPhone, setCitizenPhone] = useState('');
  const [severity, setSeverity] = useState<number>(3);
  const [notes, setNotes] = useState('');
  const [photoFile, setPhotoFile] = useState<File | null>(null);
  const [photoBlobUrl, setPhotoBlobUrl] = useState<string | undefined>();
  const [authorityPreview, setAuthorityPreview] = useState<AuthorityPreviewResponse | null>(null);
  const [infrastructure, setInfrastructure] = useState<RoadInfrastructureResponse | null>(null);
  const [locationDisplay, setLocationDisplay] = useState<string | null>(null);
  const [contextLoading, setContextLoading] = useState(false);
  const [contextError, setContextError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [submittedReport, setSubmittedReport] = useState<RoadReportResponse | null>(null);
  const [formStep, setFormStep] = useState(0);
  const [citizenName, setCitizenName] = useState('');
  const [citizenEmail, setCitizenEmail] = useState('');
  const [mapLat, setMapLat] = useState(0);
  const [mapLon, setMapLon] = useState(0);
  const [mapAddress, setMapAddress] = useState('');
  const formSteps = useRef<HTMLDivElement[]>([]);
  const { onTouchStart: swipeStart, onTouchEnd: swipeEnd } = useSwipe({
    onSwipeLeft: () => {
      if (formStep < 4) {
        const next = formStep + 1;
        setFormStep(next);
        formSteps.current[next]?.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    },
    onSwipeRight: () => {
      if (formStep > 0) {
        const prev = formStep - 1;
        setFormStep(prev);
        formSteps.current[prev]?.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    },
  });

  const setGpsLocation = useSetGpsLocation();
  const { location: gpsLocation, error: gpsError, loading: locating, refresh } = useGeolocation();

  const coordinateSignature = useMemo(() => (gpsLocation ? `${gpsLocation.lat.toFixed(4)}:${gpsLocation.lon.toFixed(4)}` : null), [gpsLocation]);

  useEffect(() => { setMounted(true); document.title = `${t('report.report_hazard')} | SafeVixAI`; }, [t]);

  useEffect(() => {
    if (!photoFile) {
      setPhotoBlobUrl(undefined);
      return;
    }
    const nextUrl = URL.createObjectURL(photoFile);
    setPhotoBlobUrl(nextUrl);
    return () => URL.revokeObjectURL(nextUrl);
  }, [photoFile]);

  useEffect(() => {
    const location = gpsLocation;
    if (!coordinateSignature || !location) return;

    const baseLocation = {
      lat: location.lat,
      lon: location.lon,
      accuracy: location.accuracy,
      timestamp: location.timestamp,
    };

    let cancelled = false;

    async function syncLocationContext() {
      setContextLoading(true);
      setContextError(null);

      const [reverseResult, authorityResult, infrastructureResult] = await Promise.allSettled([
        reverseGeocode({ lat: baseLocation.lat, lon: baseLocation.lon }),
        fetchAuthorityPreview({ lat: baseLocation.lat, lon: baseLocation.lon }),
        fetchRoadInfrastructure({ lat: baseLocation.lat, lon: baseLocation.lon }),
      ]);

      if (cancelled) return;

      let nextError: string | null = null;

      if (reverseResult.status === 'fulfilled') {
        setLocationDisplay(reverseResult.value.displayName ?? null);
        setGpsLocation({
          ...baseLocation,
          city: reverseResult.value.city ?? undefined,
          state: reverseResult.value.state ?? undefined,
          displayName: reverseResult.value.displayName ?? undefined,
        });
      } else {
        setLocationDisplay(null);
        nextError = extractApiError(
          reverseResult.reason,
          'Unable to resolve a readable address for your current coordinates.'
        );
      }

      if (authorityResult.status === 'fulfilled') {
        setAuthorityPreview(authorityResult.value);
      } else {
        setAuthorityPreview(null);
        nextError =
          nextError ??
          extractApiError(
            authorityResult.reason,
            'Road ownership lookup is temporarily unavailable.'
          );
      }

      if (infrastructureResult.status === 'fulfilled') {
        setInfrastructure(infrastructureResult.value);
      } else {
        setInfrastructure(null);
        nextError =
          nextError ??
          extractApiError(
            infrastructureResult.reason,
            'Road infrastructure data could not be loaded right now.'
          );
      }

      setContextError(nextError);
      setContextLoading(false);
    }

    void syncLocationContext();

    return () => {
      cancelled = true;
    };
  }, [coordinateSignature, gpsLocation, setGpsLocation]);

  const severityKey = severityKeyMap[severity] || 'serious';
  const severityLabelTranslated = t(`report.severities.${severityKey}`);
  const severityDescTranslated = t(`report.severities.${severityKey}_desc`);
  const locationLabel = formatLocationLabel(gpsLocation, gpsError);
  const locationSubtitle = gpsLocation ? locationDisplay ?? formatLocationSubtitle(gpsLocation) : t('report.enable_location_authority');
  const accuracyLabel = formatAccuracyLabel(gpsLocation);
  const accuracyMeters = gpsLocation?.accuracy ?? 15;
  const accuracyColor = accuracyMeters < 10 
    ? 'text-brand-light dark:text-brand-light' 
    : accuracyMeters < 30 
      ? 'text-warning dark:text-amber-400' 
      : 'text-red-500 dark:text-red-400';
  const approximateLocation = isApproximateLocation(gpsLocation);
  const photoHint = photoFile ? `${photoFile.name} - ${(photoFile.size / (1024 * 1024)).toFixed(2)} MB` : t('report.optional_photo_hint');

  const portalUrl = normalizeExternalUrl(submittedReport?.complaintPortal ?? authorityPreview?.complaintPortal ?? null);
  const helpline = submittedReport?.authorityPhone ?? authorityPreview?.helpline ?? null;
  const reportRoadName = submittedReport?.roadName ?? infrastructure?.roadName ?? authorityPreview?.roadName ?? null;
  const reportRoadNumber = submittedReport?.roadNumber ?? infrastructure?.roadNumber ?? authorityPreview?.roadNumber ?? null;
  const reportAuthority = submittedReport?.authorityName ?? authorityPreview?.authorityName ?? null;
  const reportType = submittedReport?.roadType ?? infrastructure?.roadType ?? authorityPreview?.roadType ?? null;

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!gpsLocation || !selectedType) {
      setSubmitError(t('report.form_validation_error'));
      return;
    }

    setSubmitting(true);
    setSubmitError(null);

    try {
      const response = await submitReport({
        lat: mapLat || gpsLocation.lat,
        lon: mapLon || gpsLocation.lon,
        issue_type: selectedType,
        severity,
        description: notes,
        photo: photoFile,
        citizen_phone: citizenPhone,
      });
      setSubmittedReport(response);
      track.reportSubmitted(selectedType, !!photoFile, false);
    } catch (error) {
      setSubmittedReport(null);
      setSubmitError(extractApiError(error, 'Unable to submit the report right now. Please try again.'));
    } finally {
      setSubmitting(false);
    }
  }

  async function handlePhotoChange(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0] ?? null;
    if (file) {
      const error = validateImageFile(file);
      if (error) {
        setSubmitError(error);
        return;
      }
      try {
        setContextLoading(true);
        const compressed = await compressImageFile(file);
        setPhotoFile(compressed);
      } catch (err) {
        console.error('Image compression failed, using original file:', err);
        setPhotoFile(file);
      } finally {
        setContextLoading(false);
      }
    } else {
      setPhotoFile(null);
    }
  }

  function resetForm() {
    setActiveCategory('roads');
    setSelectedType(null);
    setCitizenPhone('');
    setCitizenName('');
    setCitizenEmail('');
    setSeverity(3);
    setNotes('');
    setPhotoFile(null);
    setSubmitError(null);
    setSubmittedReport(null);
    setFormStep(0);
  }

  return (
    <div ref={pageRef} className={cx("sv-page sv-aurora relative overflow-x-hidden", !mounted && 'opacity-0')}>
      <div className="pointer-events-none absolute inset-0 z-0 overflow-hidden">
        <div className="absolute right-[-10%] top-[-12%] hidden h-[38rem] w-[38rem] rounded-full bg-cyan-500/10 blur-[150px] dark:block" />
        <div className="absolute left-[22%] top-[4%] hidden h-[20rem] w-[20rem] rounded-full bg-violet-500/8 blur-[120px] dark:block" />
        <div className="absolute bottom-[-16%] left-[-8%] hidden h-[28rem] w-[28rem] rounded-full bg-brand/12 blur-[140px] dark:block" />
      </div>

      {/* ── Unified Tactical Navigation Header ── */}
      <TerminalHeader title={t('report.report_hazard')} subtitle={t('report.report_live_road')} />
      
      <div className="lg:hidden relative z-[100]">
        <TopSearch isMapPage={false} forceShow={true} showBack={false} />
      </div>

      <main className="relative z-10 mx-auto flex w-full max-w-4xl flex-col gap-6 px-4 pb-44 pt-28 lg:pt-24 sm:px-6 lg:pb-10">
        
        {/* ── Dispatch Hero Section ── */}
        <section className="mt-4 flex flex-col gap-2">
          <div className="flex flex-wrap items-center gap-3">
            <div className="flex w-fit items-center gap-2 rounded-full border border-brand/20 bg-brand/10 px-3 py-1 dark:border-brand/15 dark:bg-brand/12">
              <span className="w-1.5 h-1.5 rounded-full bg-brand/80 animate-pulse"></span>
              <span className="text-[10px] font-semibold text-brand dark:text-brand-light uppercase tracking-widest">{t('report.report_active')}</span>
            </div>
            {approximateLocation && gpsLocation && (
              <div className="flex w-fit items-center gap-2 rounded-full border border-orange-500/20 bg-orange-500/10 px-3 py-1 dark:border-orange-400/15 dark:bg-orange-500/12">
                <span className="w-1.5 h-1.5 rounded-full bg-orange-500 animate-pulse"></span>
                <span className="text-[10px] font-semibold text-orange-600 dark:text-orange-400 uppercase tracking-widest">{t('report.approximate_gps')}</span>
              </div>
            )}
          </div>
          <div className="flex flex-col">
            <h1 className="text-2xl font-black tracking-tight text-text-1 uppercase font-space leading-tight dark:bg-gradient-to-r dark:from-white dark:via-text-1 dark:to-cyan-200 dark:bg-clip-text dark:text-transparent sm:text-3xl">
              {t('report.title')}
            </h1>
            <p className="max-w-2xl text-xs sm:text-sm font-medium text-text-3 mt-1 uppercase tracking-wider opacity-70">
              {t('report.subtitle')}
            </p>
          </div>
        </section>

        {/* ── Progress Bar ── */}
        {!submittedReport && (
          <div className="mb-2">
            <ReportProgressBar currentStep={formStep} />
          </div>
        )}

        <div className="grid gap-6">
          <section className="space-y-6">
            <SurfaceCard padding="none" className="overflow-hidden">
              <div className="min-h-[360px] sm:min-h-[420px]">
                <HazardViewfinder imageSrc={photoBlobUrl} isDetecting={contextLoading || submitting} confidence={submittedReport ? 99.4 : contextLoading ? 96.2 : 97.8} statusLabel={submittedReport ? t('report.report_uplinked') : contextLoading ? t('report.waiting_authority_lookup') : photoFile ? t('report.optional_photo_uplink') : t('report.live_authority_match')} signalLabel={accuracyLabel ?? (locating ? t('report.pending_device_fix') : t('report.pending_device_fix'))} locationLabel={gpsLocation ? `${gpsLocation.lat.toFixed(5)}, ${gpsLocation.lon.toFixed(5)}` : t('report.pending_device_fix')} viewportId={submittedReport ? submittedReport.uuid : 'RW-LIVE-REPORT-01'} />
              </div>
            </SurfaceCard>

            <div className="grid gap-4 lg:grid-cols-2">
              <SurfaceCard>
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <div className="text-[10px] font-semibold uppercase tracking-[0.22em] text-text-3">{t('report.location_lock')}</div>
                    <h2 className="mt-2 text-xl font-black tracking-tight text-text-1">{locationLabel}</h2>
                  </div>
                  <button type="button" onClick={refresh} className="inline-flex h-11 w-11 items-center justify-center rounded-lg border border-border bg-surface-2 text-text-2 transition hover:border-brand/20 hover:bg-brand/8 hover:text-brand active:scale-95" aria-label={t('report.refresh_location')}>
                    {locating ? <Loader2 size={18} className="animate-spin" /> : <RefreshCcw size={18} />}
                  </button>
                </div>
                <p className="mt-3 text-sm leading-6 text-text-2">{gpsError ?? locationSubtitle}</p>
                <div className="mt-4 grid gap-3 sm:grid-cols-2">
                  <div className="rounded-lg border border-border bg-surface-2 px-4 py-3">
                    <div className="text-[10px] font-semibold uppercase tracking-[0.22em] text-text-3">{t('report.accuracy')}</div>
                    <div className={cx("mt-2 text-sm font-semibold", gpsLocation ? accuracyColor : "text-text-1")}>{accuracyLabel ?? t('report.pending_device_fix')}</div>
                  </div>
                  <div className="rounded-lg border border-border bg-surface-2 px-4 py-3">
                    <div className="text-[10px] font-semibold uppercase tracking-[0.22em] text-text-3">{t('report.coordinates')}</div>
                    <div className="mt-2 text-sm font-semibold text-text-1">{gpsLocation ? `${gpsLocation.lat.toFixed(5)}, ${gpsLocation.lon.toFixed(5)}` : '--'}</div>
                  </div>
                </div>
                {approximateLocation && gpsLocation ? <div className="mt-4 rounded-lg border border-warning/20 bg-warning/10 px-4 py-3 text-sm font-semibold text-amber-900 dark:border-amber-400/20 dark:bg-[linear-gradient(180deg,rgba(245,158,11,0.14),rgba(120,53,15,0.16))] dark:text-warning">{t('report.approximate_location_warning')}</div> : null}
              </SurfaceCard>

              <SurfaceCard>
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <div className="text-[10px] font-semibold uppercase tracking-[0.22em] text-text-3">{t('report.evidence_capture')}</div>
                    <h2 className="mt-2 text-xl font-black tracking-tight text-text-1">{t('report.optional_photo_uplink')}</h2>
                  </div>
                  <div className="inline-flex h-11 w-11 items-center justify-center rounded-lg border border-border bg-surface-2 text-text-2"><Camera size={18} /></div>
                </div>
                <label htmlFor="hazard-photo" className="mt-4 flex cursor-pointer flex-col items-center justify-center rounded-[1.5rem] border border-dashed border-border bg-surface-2 px-5 py-8 text-center transition hover:border-brand/30 hover:bg-brand/70 dark:hover:border-brand/20 dark:hover:bg-brand/10 relative overflow-hidden group">
                  {photoBlobUrl && (
                    <div className="absolute inset-0 w-full h-full bg-black/60 z-0">
                      <Image src={photoBlobUrl} alt="Preview" fill unoptimized className="object-cover opacity-60 group-hover:opacity-40 transition" />
                    </div>
                  )}
                  <div className="relative z-10 flex flex-col items-center">
                    <div className="inline-flex h-14 w-14 items-center justify-center rounded-lg bg-brand/15 text-brand dark:bg-brand/16 dark:text-white shadow-sm"><Upload size={22} /></div>
                    <div className={`mt-4 text-sm font-semibold uppercase tracking-[0.18em] ${photoBlobUrl ? 'text-white' : 'text-text-1'}`}>{photoFile ? t('report.replace_photo') : t('report.attach_road_image')}</div>
                    <p className={`mt-2 max-w-xs text-sm ${photoBlobUrl ? 'text-white' : 'text-text-3'}`}>{photoHint}</p>
                  </div>
                </label>
                <input id="hazard-photo" type="file" accept="image/jpeg,image/png,image/webp" className="hidden" onChange={handlePhotoChange} />
              </SurfaceCard>
            </div>
          </section>

          <section className="space-y-6">
            <SurfaceCard>
              <div className="flex items-start justify-between gap-3">
                <div>
                  <div className="text-[10px] font-semibold uppercase tracking-[0.22em] text-text-3">{t('report.report_form')}</div>
                  <h2 className="mt-2 text-2xl font-black tracking-tight text-text-1">{t('report.flag_hazard_title')}</h2>
                </div>
                <div className="inline-flex h-12 w-12 items-center justify-center rounded-lg border border-border bg-surface-2 text-text-2"><Send size={18} /></div>
              </div>

              {!submittedReport ? (
                <form className="mt-6 space-y-6 sv-swipe-area" onSubmit={handleSubmit} onTouchStart={swipeStart} onTouchEnd={swipeEnd}>
                  {/* Step indicator */}
                  <div className="flex justify-center gap-1.5 pb-2 lg:hidden -mt-4">
                    {[0, 1, 2, 3, 4].map((s) => (
                      <button key={s} type="button" onClick={() => { setFormStep(s); formSteps.current[s]?.scrollIntoView({ behavior: 'smooth', block: 'start' }); }} className={`h-1.5 rounded-full transition-all duration-300 ${formStep === s ? 'w-6 bg-brand-light' : 'w-2 bg-border'}`} aria-label={`Step ${s + 1}`} />
                    ))}
                    <span className="text-[9px] font-semibold text-text-3 uppercase tracking-widest ml-2 self-center">Swipe ↔</span>
                  </div>
                  {/* Step 0: Category & Type */}
                  <div ref={(el) => { if (el) formSteps.current[0] = el; }}>
                  {/* Category Tabs */}
                  <div>
                    <div className="text-[10px] font-semibold uppercase tracking-[0.22em] text-text-3">{t('report.incident_category')}</div>
                    <div className="mt-3 grid grid-cols-3 gap-2">
                      {(['roads', 'traffic', 'streetlight'] as const).map((cat) => {
                        const active = activeCategory === cat;
                        return (
                          <button
                            key={cat}
                            type="button"
                            onClick={() => {
                              setActiveCategory(cat);
                              setSelectedType(null);
                            }}
                            className={cx(
                              'rounded-xl border px-3 py-3 text-center transition font-semibold uppercase tracking-[0.1em] text-xs',
                              active
                                ? 'border-brand bg-brand/10 text-brand-light'
                                : 'border-border bg-surface-2 text-text-2 hover:bg-surface-3'
                            )}
                          >
                            {cat === 'roads' ? '🛣️ ' + t('report.roads_label') : cat === 'traffic' ? '🚦 ' + t('report.traffic_label') : '💡 ' + t('report.streetlights_label')}
                          </button>
                        );
                      })}
                    </div>
                  </div>

                  {/* Category specific sub-types */}
                  <div>
                    <div className="text-[10px] font-semibold uppercase tracking-[0.22em] text-text-3">{t('report.hazard_type')}</div>
                    <div className="mt-3 grid gap-3 sm:grid-cols-2">
                      {ISSUE_OPTIONS_BY_CATEGORY[activeCategory].map(([value], index) => {
                        const active = value === selectedType;
                        const activeAccent = [
                          'border-brand/30 bg-brand/10 text-brand-light dark:border-brand-light/30',
                          'border-orange-500/30 bg-orange-500/10 text-orange-400',
                          'border-cyan-500/30 bg-cyan-500/10 text-cyan-400',
                          'border-emerald-500/30 bg-emerald-500/10 text-emerald-400',
                          'border-purple-500/30 bg-purple-500/10 text-purple-400',
                          'border-rose-500/30 bg-rose-500/10 text-rose-400',
                        ][index % 6];
                        return (
                          <button
                            key={value}
                            type="button"
                            onClick={() => setSelectedType(value)}
                            className={cx(
                              'rounded-[1.5rem] border px-4 py-4 text-left transition',
                              active
                                ? activeAccent
                                : 'border-border bg-surface-2 text-text-2 hover:bg-surface-3'
                            )}
                          >
                            <div className="text-sm font-semibold uppercase tracking-[0.16em]">{t(`report.issue_types.${value}`)}</div>
                            <p className="mt-2 text-xs font-medium opacity-80">{t(`report.issue_types.${value}_desc`)}</p>
                          </button>
                        );
                      })}
                    </div>
                  </div>
                  </div>

                  {/* Step 1: Location (Map Picker) */}
                  <div ref={(el) => { if (el) formSteps.current[1] = el; }}>
                  <div>
                    <div className="text-[10px] font-semibold uppercase tracking-[0.22em] text-text-3">Pinpoint Location</div>
                    <p className="mt-1 text-xs text-text-3">Drag the pin to mark the exact hazard location</p>
                    <div className="mt-3">
                      <LocationPicker
                        lat={gpsLocation?.lat ?? 13.0827}
                        lon={gpsLocation?.lon ?? 80.2707}
                        onLocationChange={(lat, lon, addr) => {
                          setMapLat(lat);
                          setMapLon(lon);
                          setMapAddress(addr);
                        }}
                      />
                    </div>
                    {mapAddress && (
                      <div className="mt-2 text-xs text-text-2"><MapPin size={12} className="inline mr-1" />{mapAddress}</div>
                    )}
                  </div>
                  </div>

                  {/* Step 2: Details (Severity, Notes) */}
                  <div ref={(el) => { if (el) formSteps.current[2] = el; }}>

                  <div>
                    <div className="flex items-center justify-between gap-3">
                      <div className="text-[10px] font-semibold uppercase tracking-[0.22em] text-text-3">{t('report.severity')}</div>
                      <div className="text-sm font-semibold text-text-2">{severityLabelTranslated} - {severityDescTranslated}</div>
                    </div>
                    <div className="mt-3 grid grid-cols-5 gap-2">
                      {SEVERITY_OPTIONS.map(([value]) => {
                        const active = value === severity;
                        const severityKeyOpt = severityKeyMap[value] || 'serious';
                        return (
                          <button key={value} type="button" onClick={() => setSeverity(value)} className={cx('rounded-lg border px-3 py-4 text-center transition', active ? value >= 4 ? 'border-red-500 bg-red-500 text-white shadow-lg shadow-red-500/20' : 'border-brand bg-brand/80 text-white shadow-lg shadow-brand/20' : 'border-border bg-surface-2 text-text-2 hover:border-border dark:text-text-1')}>
                            <div className="text-lg font-black leading-none">{value}</div>
                            <div className="mt-2 text-[10px] font-semibold uppercase tracking-[0.18em]">{t(`report.severities.${severityKeyOpt}`)}</div>
                          </button>
                        );
                      })}
                    </div>
                  </div>

                  <div>
                    <div className="flex items-center justify-between gap-3">
                      <div className="text-[10px] font-semibold uppercase tracking-[0.22em] text-text-3">{t('report.notes_label')}</div>
                      <div className="text-xs font-semibold text-text-3">{notes.trim().length}/480</div>
                    </div>
                    <textarea value={notes} onChange={(event) => setNotes(event.target.value.slice(0, 480))} placeholder={t('report.notes_placeholder')} aria-label={t('report.notes_label')} className="mt-3 min-h-[140px] w-full rounded-[1.5rem] border border-border bg-surface-2 px-4 py-4 text-sm font-medium text-text-1 outline-none transition placeholder:text-text-3 focus:border-brand/40 focus:bg-white dark:focus:border-brand/40 dark:focus:bg-surface-3" />
                  </div>
                  </div>

                  {/* Step 3: Contact Info */}
                  <div ref={(el) => { if (el) formSteps.current[3] = el; }}>
                  <div>
                    <div className="text-[10px] font-semibold uppercase tracking-[0.22em] text-text-3 mb-3">Contact Information</div>
                    <p className="text-xs text-text-3 mb-4">Optional — allows authorities to reach you for updates</p>
                    <div className="space-y-4">
                      <div>
                        <label htmlFor="report-name" className="text-[10px] font-semibold uppercase tracking-[0.22em] text-text-3">Full Name</label>
                        <input
                          id="report-name"
                          type="text"
                          value={citizenName}
                          onChange={(e) => setCitizenName(e.target.value)}
                          placeholder="Your full name (optional)"
                          aria-label="Full Name"
                          className="mt-2 w-full rounded-[1.5rem] border border-border bg-surface-2 px-4 py-3 text-sm font-medium text-text-1 outline-none transition placeholder:text-text-3 focus:border-brand/40 focus:bg-surface-3"
                        />
                      </div>
                      <div>
                        <label htmlFor="report-email" className="text-[10px] font-semibold uppercase tracking-[0.22em] text-text-3">Email</label>
                        <input
                          id="report-email"
                          type="email"
                          value={citizenEmail}
                          onChange={(e) => setCitizenEmail(e.target.value)}
                          placeholder="your@email.com (optional)"
                          aria-label="Email"
                          className="mt-2 w-full rounded-[1.5rem] border border-border bg-surface-2 px-4 py-3 text-sm font-medium text-text-1 outline-none transition placeholder:text-text-3 focus:border-brand/40 focus:bg-surface-3"
                        />
                      </div>
                      <div>
                        <label htmlFor="report-phone" className="text-[10px] font-semibold uppercase tracking-[0.22em] text-text-3">{t('report.your_phone')}</label>
                        <input
                          id="report-phone"
                          type="tel"
                          value={citizenPhone}
                          onChange={(e) => setCitizenPhone(e.target.value.replace(/[^0-9+]/g, '').slice(0, 15))}
                          placeholder={t('report.phone_placeholder')}
                          aria-label={t('report.your_phone')}
                          className="mt-2 w-full rounded-[1.5rem] border border-border bg-surface-2 px-4 py-3 text-sm font-medium text-text-1 outline-none transition placeholder:text-text-3 focus:border-brand/40 focus:bg-surface-3"
                        />
                      </div>
                    </div>
                  </div>
                  </div>

                  {/* Step 4: Review & Submit */}
                  <div ref={(el) => { if (el) formSteps.current[4] = el; }}>

                  {/* Review Summary */}
                  <div className="rounded-xl border border-border bg-surface-2/50 p-4 space-y-2 mb-4">
                    <div className="text-[10px] font-bold uppercase tracking-widest text-text-3 mb-3">Review Summary</div>
                    <div className="text-xs"><span className="text-text-3 font-semibold">Category:</span> <span className="text-text-1 font-bold capitalize">{activeCategory}</span></div>
                    <div className="text-xs"><span className="text-text-3 font-semibold">Issue:</span> <span className="text-text-1 font-bold">{selectedType ?? '—'}</span></div>
                    <div className="text-xs"><span className="text-text-3 font-semibold">Severity:</span> <span className="text-text-1 font-bold">Level {severity}</span></div>
                    {mapAddress && <div className="text-xs"><span className="text-text-3 font-semibold">Location:</span> <span className="text-text-1">{mapAddress}</span></div>}
                    {citizenName && <div className="text-xs"><span className="text-text-3 font-semibold">Name:</span> <span className="text-text-1">{citizenName}</span></div>}
                    {citizenPhone && <div className="text-xs"><span className="text-text-3 font-semibold">Phone:</span> <span className="text-text-1">{citizenPhone}</span></div>}
                    {notes && <div className="text-xs"><span className="text-text-3 font-semibold">Notes:</span> <span className="text-text-1">{notes.slice(0, 100)}{notes.length > 100 ? '...' : ''}</span></div>}
                    {photoFile && <div className="text-xs"><span className="text-text-3 font-semibold">Photo:</span> <span className="text-text-1">{photoFile.name}</span></div>}
                  </div>

                  {submitError ? <div className="rounded-[1.5rem] border border-emergency/20 bg-emergency/10 px-4 py-3 text-sm font-semibold text-red-900 dark:border-red-400/20 dark:bg-red-500/10 dark:text-red-100">{submitError}</div> : null}

                  <div className="flex flex-col gap-3 sm:flex-row">
                    <button type="submit" disabled={submitting || !gpsLocation || !selectedType} className="inline-flex flex-1 items-center justify-center gap-3 rounded-[1.6rem] bg-gradient-to-r from-orange-500 via-rose-500 to-red-500 px-5 py-4 text-sm font-semibold uppercase tracking-[0.22em] text-white shadow-[0_24px_80px_rgba(239,68,68,0.24)] transition hover:translate-y-[-1px] disabled:cursor-not-allowed disabled:opacity-50 disabled:hover:translate-y-0">
                      {submitting ? <Loader2 size={18} className="animate-spin" /> : <Send size={18} />}
                      {submitting ? t('report.submitting') : t('report.submit_button')}
                    </button>
                    <button type="button" onClick={resetForm} className="inline-flex items-center justify-center gap-3 rounded-[1.6rem] border border-border bg-surface-2 px-5 py-4 text-sm font-semibold uppercase tracking-[0.18em] text-text-2 transition hover:border-border hover:bg-white dark:hover:border-white/20 dark:hover:bg-white/10">
                      <RefreshCcw size={18} />{t('report.reset')}
                    </button>
                  </div>
                  </div>
                </form>
              ) : (
                <div className="mt-8 flex flex-col items-center justify-center text-center py-10">
                  <div className="w-24 h-24 rounded-full bg-brand-light/20 flex items-center justify-center animate-pulse mb-6">
                    <CheckCircle2 size={48} className="text-brand-light" />
                  </div>
                  <h3 className="text-3xl font-black text-text-1 font-space tracking-tight">{t('report.report_uplinked')}</h3>
                  <p className="mt-3 text-text-3 max-w-sm">{t('report.report_uplinked_desc')}</p>
                </div>
              )}
            </SurfaceCard>
                  {submittedReport ? (
                <div>
                  <SurfaceCard className="border-brand-light/20 bg-brand-light/10 dark:border-brand-light/20 dark:bg-brand-light/10">
                    <div className="flex items-start justify-between gap-4">
                      <div>
                        <span className="inline-flex items-center gap-2 rounded-full border border-brand-light/20 bg-brand-light/15 px-3 py-1 text-[10px] font-semibold uppercase tracking-[0.1em] text-brand dark:border-brand-light/20 dark:bg-brand-light/10 dark:text-brand-light"><span className="h-1.5 w-1.5 rounded-full bg-current" />{t('report.report_uplinked')}</span>
                        <h3 className="mt-3 text-2xl font-black tracking-tight text-text-1 dark:text-brand-light">{t('report.complaint_reference', { ref: submittedReport.complaintRef ?? submittedReport.uuid })}</h3>
                        <p className="mt-2 text-sm font-semibold text-text-2 dark:text-brand-light">{t('report.complaint_tagged', { authority: submittedReport.authorityName, road: [submittedReport.roadNumber, submittedReport.roadName].filter(Boolean).join(' - ') || submittedReport.roadType })}</p>
                      </div>
                      <div className="inline-flex h-14 w-14 items-center justify-center rounded-lg bg-brand text-white shadow-lg shadow-brand/20"><CheckCircle2 size={22} /></div>
                    </div>

                    {submittedReport.duplicateOfUuid && (
                      <div className="mt-4 rounded-lg border border-amber-500/20 bg-amber-500/10 px-4 py-3 text-sm font-semibold text-amber-600 dark:border-amber-400/20 dark:bg-amber-500/12 dark:text-warning flex items-center gap-3">
                        <AlertTriangle className="animate-pulse flex-shrink-0" size={18} />
                        <span>{t('report.duplicate_detected')}</span>
                      </div>
                    )}

                    <div className="mt-5 grid gap-3 sm:grid-cols-2">
                      <div className="rounded-lg border border-brand-light/20 bg-white/80 px-4 py-3 dark:border-brand-light/20 dark:bg-brand/10">
                        <div className="text-[10px] font-semibold uppercase tracking-[0.22em] text-brand dark:text-brand-light">{t('report.authority_desk')}</div>
                        <div className="mt-2 text-lg font-black text-text-1 dark:text-brand-light">{submittedReport.authorityName}</div>
                        <a href={`tel:${submittedReport.authorityPhone}`} className="mt-2 inline-flex items-center gap-2 text-sm font-semibold text-brand underline decoration-brand-light underline-offset-4 dark:text-brand-light"><Phone size={14} />{submittedReport.authorityPhone}</a>
                      </div>
                      <div className="rounded-lg border border-brand-light/20 bg-white/80 px-4 py-3 dark:border-brand-light/20 dark:bg-brand/10">
                        <div className="text-[10px] font-semibold uppercase tracking-[0.22em] text-brand dark:text-brand-light">{t('report.tagged_road_asset')}</div>
                        <div className="mt-2 text-lg font-black text-text-1 dark:text-brand-light">{[submittedReport.roadNumber, submittedReport.roadName].filter(Boolean).join(' - ') || submittedReport.roadType}</div>
                        <div className="mt-2 text-sm font-semibold text-text-2 dark:text-brand-light">{submittedReport.roadType}</div>
                      </div>
                      {submittedReport.slaDeadline && (
                        <div className="rounded-lg border border-brand-light/20 bg-white/80 px-4 py-3 dark:border-brand-light/20 dark:bg-brand/10 sm:col-span-2">
                          <div className="text-[10px] font-semibold uppercase tracking-[0.22em] text-brand dark:text-brand-light">{t('report.sla_resolution_target')}</div>
                          <div className="mt-2 text-lg font-black text-text-1 dark:text-brand-light">
                            {new Date(submittedReport.slaDeadline).toLocaleString('en-IN', { dateStyle: 'medium', timeStyle: 'short' })}
                          </div>
                          <div className="mt-2 text-xs font-semibold text-text-3 dark:text-brand-light">{t('report.guaranteed_response')}</div>
                        </div>
                      )}
                    </div>
                    <div className="mt-5 flex flex-wrap gap-3">
                      <Link href={`/report/track?ref=${submittedReport.complaintRef ?? submittedReport.uuid}`} className="inline-flex items-center justify-center gap-2 rounded-lg bg-cyan-600 px-4 py-3 text-sm font-semibold uppercase tracking-[0.1em] text-white shadow-lg shadow-cyan-600/20 transition hover:bg-cyan-500"><MapPin size={16} />{t('report.track_progress')}</Link>
                      {portalUrl ? <a href={portalUrl} target="_blank" rel="noreferrer" className="inline-flex items-center justify-center gap-2 rounded-lg bg-brand px-4 py-3 text-sm font-semibold uppercase tracking-[0.1em] text-white shadow-lg shadow-brand/20 transition hover:bg-brand-light"><Navigation size={16} />{t('report.open_complaint_portal')}</a> : null}
                      <button type="button" onClick={resetForm} className="inline-flex items-center justify-center gap-2 rounded-lg border border-brand-light/20 bg-white px-4 py-3 text-sm font-semibold uppercase tracking-[0.18em] text-brand transition hover:border-brand-light dark:border-brand-light/20 dark:bg-brand/10 dark:text-brand-light dark:hover:bg-brand/20"><RefreshCcw size={16} />{t('report.file_another_report')}</button>
                    </div>
                  </SurfaceCard>
                </div>
              ) : null}

            <SurfaceCard>
              <div className="flex items-start justify-between gap-3">
                <div>
                  <div className="text-[10px] font-semibold uppercase tracking-[0.22em] text-text-3">{t('report.live_authority_match')}</div>
                  <h2 className="mt-2 text-xl font-black tracking-tight text-text-1">{reportAuthority ?? t('report.waiting_authority_lookup')}</h2>
                </div>
                <div className="inline-flex h-12 w-12 items-center justify-center rounded-lg border border-border bg-surface-2 text-text-2">{contextLoading ? <Loader2 size={18} className="animate-spin" /> : <ShieldAlert size={18} />}</div>
              </div>
              {contextError ? <div className="mt-4 rounded-lg border border-warning/20 bg-warning/10 px-4 py-3 text-sm font-semibold text-amber-900 dark:border-amber-400/20 dark:bg-[linear-gradient(180deg,rgba(245,158,11,0.14),rgba(120,53,15,0.16))] dark:text-warning">{contextError}</div> : null}
              <div className="mt-4 divide-y divide-border">
                <div className="flex items-start justify-between gap-4 py-2"><div className="text-[10px] font-semibold uppercase tracking-[0.22em] text-text-3">{t('report.road')}</div><div className="max-w-[65%] text-right text-sm font-semibold text-text-1">{[reportRoadNumber, reportRoadName].filter(Boolean).join(' - ') || reportType || t('report.not_published')}</div></div>
                <div className="flex items-start justify-between gap-4 py-2"><div className="text-[10px] font-semibold uppercase tracking-[0.22em] text-text-3">{t('report.authority')}</div><div className="max-w-[65%] text-right text-sm font-semibold text-text-1">{reportAuthority ?? t('report.not_published')}</div></div>
                <div className="flex items-start justify-between gap-4 py-2"><div className="text-[10px] font-semibold uppercase tracking-[0.22em] text-text-3">{t('report.helpline', { phone: '' }).replace(': ', '').trim()}</div><div className="max-w-[65%] text-right text-sm font-semibold text-text-1">{helpline ? <a href={`tel:${helpline}`} className="text-brand dark:text-brand-light underline decoration-brand-light underline-offset-4 hover:text-brand dark:text-brand-light">{helpline}</a> : t('report.not_published')}</div></div>
                <div className="flex items-start justify-between gap-4 py-2"><div className="text-[10px] font-semibold uppercase tracking-[0.22em] text-text-3">{t('report.portal')}</div><div className="max-w-[65%] text-right text-sm font-semibold text-text-1">{portalUrl ? <a href={portalUrl} target="_blank" rel="noreferrer" className="text-brand dark:text-brand-light underline decoration-brand-light underline-offset-4 hover:text-brand dark:text-brand-light">{t('report.open_complaint_portal')}</a> : t('report.portal_not_listed')}</div></div>
                <div className="flex items-start justify-between gap-4 py-2"><div className="text-[10px] font-semibold uppercase tracking-[0.22em] text-text-3">{t('report.escalation')}</div><div className="max-w-[65%] text-right text-sm font-semibold text-text-1">{authorityPreview?.escalationPath ?? t('report.not_published')}</div></div>
                <div className="flex items-start justify-between gap-4 py-2"><div className="text-[10px] font-semibold uppercase tracking-[0.22em] text-text-3">{t('report.exec_engineer')}</div><div className="max-w-[65%] text-right text-sm font-semibold text-text-1">{authorityPreview?.execEngineer ?? infrastructure?.execEngineer ?? t('report.not_published')}</div></div>
              </div>
            </SurfaceCard>

            <SurfaceCard>
              <div className="flex items-start justify-between gap-3">
                <div>
                  <div className="text-[10px] font-semibold uppercase tracking-[0.22em] text-text-3">{t('report.road_asset_intelligence')}</div>
                  <h2 className="mt-2 text-xl font-black tracking-tight text-text-1">{reportRoadNumber ?? reportRoadName ?? t('report.metadata_pending')}</h2>
                </div>
                <div className="inline-flex h-12 w-12 items-center justify-center rounded-lg border border-border bg-surface-2 text-text-2"><MapPin size={18} /></div>
              </div>
              <div className="mt-4 grid gap-3 sm:grid-cols-2">
                <div className="rounded-lg border border-border bg-surface-2 px-4 py-3"><div className="text-[10px] font-semibold uppercase tracking-[0.22em] text-text-3">{t('report.road_type')}</div><div className="mt-2 text-sm font-semibold text-text-1">{reportType ?? t('report.waiting_authority_lookup')}</div></div>
                <div className="rounded-lg border border-border bg-surface-2 px-4 py-3"><div className="text-[10px] font-semibold uppercase tracking-[0.22em] text-text-3">{t('report.contractor')}</div><div className="mt-2 text-sm font-semibold text-text-1">{infrastructure?.contractorName ?? submittedReport?.contractorName ?? t('report.not_published')}</div></div>
                <div className="rounded-lg border border-border bg-surface-2 px-4 py-3"><div className="text-[10px] font-semibold uppercase tracking-[0.22em] text-text-3">{t('report.budget_sanctioned')}</div><div className="mt-2 text-sm font-semibold text-text-1">{formatMoney(submittedReport?.budgetSanctioned ?? infrastructure?.budgetSanctioned ?? null)}</div></div>
                <div className="rounded-lg border border-border bg-surface-2 px-4 py-3"><div className="text-[10px] font-semibold uppercase tracking-[0.22em] text-text-3">{t('report.next_maintenance')}</div><div className="mt-2 text-sm font-semibold text-text-1">{submittedReport?.nextMaintenance ?? infrastructure?.nextMaintenance ?? authorityPreview?.nextMaintenance ?? t('report.not_scheduled')}</div></div>
              </div>
            </SurfaceCard>

            {/* Powered by SafeVixAI notice */}
            <SurfaceCard className="border-border">
              <div className="flex items-start gap-3">
                <div className="mt-0.5 inline-flex h-11 w-11 items-center justify-center rounded-lg bg-brand text-white dark:bg-brand-light dark:text-text-1"><ShieldAlert size={18} /></div>
                <div>
                  <div className="text-[10px] font-semibold uppercase tracking-[0.1em] text-text-3">{t('report.platform_title')}</div>
                  <p className="mt-2 text-sm font-semibold leading-6 text-text-2">{t('report.platform_desc')}</p>
                </div>
              </div>
            </SurfaceCard>
          </section>
        </div>
      </main>

      <div className="fixed right-4 top-[92px] z-30 flex flex-col gap-3 lg:right-8">
        <button type="button" onClick={refresh} className="inline-flex h-14 w-14 items-center justify-center rounded-full border border-border bg-surface-1/75 text-text-2 shadow-[0_20px_40px_rgba(15,23,42,0.12)] backdrop-blur-xl transition hover:-translate-y-0.5 hover:text-brand" aria-label={t('report.refresh_location')}>
          {locating ? <Loader2 size={20} className="animate-spin" /> : <Navigation size={20} />}
        </button>
      </div>

      <div className="fixed bottom-[calc(6.5rem+env(safe-area-inset-bottom))] right-4 z-30 lg:hidden">
        <Link href="/locator" className="inline-flex items-center gap-2 rounded-full border border-border bg-surface-1/85 px-4 py-3 text-sm font-semibold uppercase tracking-[0.18em] text-text-1 shadow-xl backdrop-blur-xl">
          <Mic size={16} />{t('report.nearby_help')}
        </Link>
      </div>

    </div>
  );
}

