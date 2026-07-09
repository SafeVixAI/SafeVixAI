// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

'use client';

import React, { useEffect, useState, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { useRouter } from 'next/navigation';
import Image from 'next/image';
import {
  MapPin,
  Clock,
  Compass,
  Navigation,
  Camera,
  CheckCircle2,
  AlertTriangle,
  User,
  LogOut,
  FileText,
  ChevronRight,
  Loader2,
  ThumbsUp,
} from 'lucide-react';
import { client } from '@/lib/api';
import { useAppStore } from '@/lib/store';
import { useShallow } from 'zustand/react/shallow';
import { TerminalHeader } from '@/components/ui/TerminalHeader';
import { SurfaceCard } from '@/components/ui/SurfaceCard';

interface RoadIssueItem {
  uuid: string;
  issue_type: string;
  severity: number;
  description?: string | null;
  lat: number;
  lon: number;
  location_address?: string | null;
  road_name?: string | null;
  road_type?: string | null;
  road_number?: string | null;
  authority_name?: string | null;
  status: string;
  created_at: string;
  category?: string | null;
  sub_category?: string | null;
  ward_id?: string | null;
  ward_name?: string | null;
  sla_deadline?: string | null;
  before_photo_url?: string | null;
  after_photo_url?: string | null;
  confirmation_count: number;
}

interface OfficerProfile {
  id: string;
  name: string;
  phone?: string | null;
  email: string;
  role: string;
  ward_id: string;
  department: string;
  is_active: boolean;
  last_checkin?: string | null;
}

export default function OfficerFieldClient() {
  const { t } = useTranslation('common');
  const router = useRouter();
  const { isAuthenticated, clearAuth } = useAppStore(useShallow((s) => ({ isAuthenticated: s.isAuthenticated, clearAuth: s.clearAuth })));

  const [officer, setOfficer] = useState<OfficerProfile | null>(null);
  const [workload, setWorkload] = useState<RoadIssueItem[]>([]);
  const [selectedIssue, setSelectedIssue] = useState<RoadIssueItem | null>(null);

  // UI state
  const [loading, setLoading] = useState(true);
  const [checkingIn, setCheckingIn] = useState(false);
  const [checkinSuccess, setCheckinSuccess] = useState(false);
  const [lastCheckinTime, setLastCheckinTime] = useState<string | null>(null);
  const [resolving, setResolving] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Resolution Form
  const [resNotes, setResNotes] = useState('');
  const [resPhoto, setResPhoto] = useState<File | null>(null);
  const [photoPreview, setPhotoPreview] = useState<string | null>(null);

  const loadOfficerData = useCallback(async () => {
    setLoading(true);
    setErrorMsg(null);
    try {
      const profileRes = await client.get('/api/v1/officers/me');
      setOfficer(profileRes.data);
      if (profileRes.data.last_checkin) {
        setLastCheckinTime(new Date(profileRes.data.last_checkin).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' }));
      }

      const workloadRes = await client.get('/api/v1/officers/me/workload');
      setWorkload(workloadRes.data);
    } catch (err: any) {
      console.error(err);
      if (err.response?.status === 401 || err.response?.status === 403) {
        setErrorMsg("Unauthorized. Redirecting to login...");
        setTimeout(() => router.push('/login'), 1500);
      } else {
        setErrorMsg("Failed to synchronize field database. Check internet connection.");
      }
    } finally {
      setLoading(false);
    }
  }, [router]);

  useEffect(() => {
    document.title = 'SafeVixAI | Field Operator';
    if (!isAuthenticated) {
      router.push('/login');
    } else {
      loadOfficerData();
    }
  }, [isAuthenticated, loadOfficerData, router]);

  // Escape key closes the issue detail drawer
  useEffect(() => {
    if (!selectedIssue) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setSelectedIssue(null);
        setResPhoto(null);
        setPhotoPreview(null);
        setResNotes('');
        setErrorMsg(null);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [selectedIssue]);

  // Handle GPS Checkin
  const handleCheckin = () => {
    /* istanbul ignore if */if (!navigator.geolocation) {
      /* istanbul ignore next */setErrorMsg("GPS geolocation is unsupported on this device.");
      /* istanbul ignore next */return;
    }

    setCheckingIn(true);
    setCheckinSuccess(false);
    setErrorMsg(null);

    /* istanbul ignore next */navigator.geolocation.getCurrentPosition(
      async (pos) => {
        try {
          const lat = pos.coords.latitude;
          const lon = pos.coords.longitude;

          const res = await client.post('/api/v1/officers/checkin', { lat, lon });
          setCheckinSuccess(true);
          setLastCheckinTime(new Date(res.data.last_checkin).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' }));
          
          // Re-fetch profile to sync ward geofence info
          const profileRes = await client.get('/api/v1/officers/me');
          setOfficer(profileRes.data);

          setTimeout(() => setCheckinSuccess(false), 4000);
        } catch (err: any) {
          console.error(err);
          setErrorMsg("Uplink failed. Location update refused by base station.");
        } finally {
          setCheckingIn(false);
        }
      },
      (err) => {
        console.error(err);
        setErrorMsg("GPS lock failed. Ensure location services are enabled.");
        setCheckingIn(false);
      },
      { enableHighAccuracy: true, timeout: 10000 }
    );
  };

  // Image capture handler
  const handlePhotoChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setResPhoto(file);
    const reader = new FileReader();
    reader.onloadend = () => {
      setPhotoPreview(reader.result as string);
    };
    reader.readAsDataURL(file);
  };

  // Submit Resolution
  const handleResolve = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedIssue) return;

    setResolving(true);
    setErrorMsg(null);

    try {
      const formData = new FormData();
      if (resPhoto) {
        formData.append('after_photo', resPhoto);
      }
      if (resNotes.trim()) {
        formData.append('notes', resNotes);
      }

      await client.post(`/api/v1/roads/report/${selectedIssue.uuid}/resolve`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      // Filter resolved issue out of the workload
      setWorkload(prev => prev.filter(item => item.uuid !== selectedIssue.uuid));
      setSelectedIssue(null);
      setResNotes('');
      setResPhoto(null);
      setPhotoPreview(null);

      // Re-trigger load to sync
      loadOfficerData();
    } catch (err: any) {
      console.error(err);
      setErrorMsg("Failed to upload resolution evidence. Please try again.");
    } finally {
      setResolving(false);
    }
  };

  // Navigation Deeplinks
  const openNavigation = (lat: number, lon: number) => {
    const url = `https://www.google.com/maps/search/?api=1&query=${lat},${lon}`;
    window.open(url, '_blank', 'noopener,noreferrer');
  };

  const getCategoryColor = (cat?: string | null) => {
    switch (cat) {
      case 'roads': return 'text-cyan-400 border-cyan-500/20 bg-cyan-500/10';
      case 'traffic': return 'text-orange-400 border-orange-500/20 bg-orange-500/10';
      case 'streetlight': return 'text-purple-400 border-purple-500/20 bg-purple-500/10';
      default: return 'text-slate-400 border-slate-500/20 bg-slate-500/10';
    }
  };

  const getSeverityBadge = (sev: number) => {
    if (sev >= 5) return 'bg-red-500/25 border-red-500/40 text-red-400';
    if (sev == 4) return 'bg-orange-500/20 border-orange-500/30 text-orange-400';
    if (sev == 3) return 'bg-amber-500/20 border-amber-500/30 text-amber-400';
    return 'bg-slate-500/20 border-slate-500/30 text-slate-300';
  };

  const getSlaCountdown = (deadline?: string | null) => {
    if (!deadline) return 'SLA Excluded';
    const diff = new Date(deadline).getTime() - Date.now();
    if (diff <= 0) return 'SLA BREACHED';
    
    const hours = Math.floor(diff / (1000 * 60 * 60));
    const mins = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
    return `${hours}h ${mins}m left`;
  };

  const handleLogout = () => {
    clearAuth();
    router.replace('/login');
  };

  return (
    <div className="sv-page sv-aurora relative min-h-screen bg-surface-1 dark:bg-slate-950 text-text-1 dark:text-slate-100 pb-24">
      <h1 className="sr-only">Field Response Uplink</h1>
      {/* ── Background aurora glow effects ── */}
      <div className="pointer-events-none absolute inset-0 z-0 overflow-hidden">
        <div className="absolute right-[-10%] top-[-10%] h-[32rem] w-[32rem] rounded-full bg-emerald-500/5 blur-[120px]" />
        <div className="absolute left-[-5%] bottom-[-10%] h-[28rem] w-[28rem] rounded-full bg-brand/5 blur-[130px]" />
      </div>

      <TerminalHeader title="Field Response Uplink" subtitle="CIVIC DISPATCH CONTROL UNIT" />

      <main className="relative z-10 mx-auto flex w-full max-w-4xl flex-col gap-6 px-4 pt-28 sm:px-6">
        
        {/* Error notification banner */}
        {errorMsg && (
          <div className="rounded-xl border border-red-500/20 bg-red-500/10 px-4 py-3.5 text-xs font-semibold text-red-400 flex items-center gap-3">
            <AlertTriangle size={16} className="flex-shrink-0" />
            <span>{errorMsg}</span>
          </div>
        )}

        {/* Loading overlay */}
        {loading ? (
          <div className="flex flex-col items-center justify-center py-20 gap-3">
            <Loader2 size={36} className="animate-spin text-brand" />
            <div className="text-xs font-black uppercase tracking-[0.2em] text-text-3">{t('officer.sync_matrix', 'Syncing Local Field Matrix...')}</div>
          </div>
        ) : (
          <>
            {/* ── SECTION 1: OFFICER SUMMARY PANEL ── */}
            {officer && (
              <SurfaceCard className="relative overflow-hidden">
                <div className="flex flex-col justify-between md:flex-row md:items-center gap-6">
                  {/* Officer credentials */}
                  <div className="flex items-start gap-4">
                    <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-brand/20 border border-brand/30 text-brand-light">
                      <User size={24} />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <h2 className="text-lg font-black font-space tracking-tight text-text-1 uppercase">
                          {officer.name}
                        </h2>
                        <span className="rounded bg-brand/10 border border-brand/20 px-2 py-0.5 text-[9px] font-black uppercase tracking-wider text-brand-light">
                          {officer.role.replace('_', ' ')}
                        </span>
                      </div>
                      <p className="text-[10px] font-bold text-text-3 uppercase tracking-wider mt-1">
                        {officer.department} · {officer.ward_id.replace('ward_', '').replace('_', ' ').toUpperCase()}
                      </p>
                    </div>
                  </div>

                  {/* Actions (GPS Checkin & Logout) */}
                  <div className="flex flex-wrap items-center gap-3">
                    <button
                      onClick={handleCheckin}
                      disabled={checkingIn}
                      className={`relative flex items-center justify-center gap-2 rounded-xl px-5 py-3 text-xs font-bold uppercase tracking-widest border transition-all ${
                        checkinSuccess
                          ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400'
                          : 'bg-brand/10 hover:bg-brand/20 border-brand/20 text-brand-light shadow-md shadow-brand/10'
                      }`}
                    >
                            {checkingIn ? (
                        <>
                          <Loader2 size={13} className="animate-spin" />
                          <span>{t('officer.acquiring_gps', 'Acquiring GPS...')}</span>
                        </>
                      ) : checkinSuccess ? (
                        <>
                          <CheckCircle2 size={13} />
                          <span>{t('officer.location_uplinked', 'Location Uplinked!')}</span>
                        </>
                      ) : (
                        <>
                          <Compass size={13} className="animate-pulse" />
                          <span>{t('officer.broadcast_gps', 'Broadcast GPS')}</span>
                        </>
                      )}
                    </button>

                    <button
                      onClick={handleLogout}
                      className="flex items-center justify-center gap-2 rounded-xl bg-surface-2 dark:bg-slate-900 border border-border px-4 py-3 text-xs font-bold uppercase tracking-widest text-text-2 hover:text-white transition-all hover:bg-surface-3 dark:hover:bg-slate-800"
                    >
                      <LogOut size={13} />
                      <span className="hidden sm:inline">{t('officer.stand_down', 'Stand Down')}</span>
                    </button>
                  </div>
                </div>

                {/* Last checkin status breadcrumb */}
                <div className="mt-4 pt-4 border-t border-border flex flex-wrap gap-4 items-center justify-between text-[10px] font-bold text-text-3 uppercase tracking-wider">
                  <div className="flex items-center gap-2">
                    <span className="relative flex h-2 w-2">
                      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                      <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
                    </span>
                    <span>{t('officer.status_duty', 'Status: ACTIVE FIELD DUTY')}</span>
                  </div>
                  <div>
                    {t('officer.last_checkin', 'Last check-in: ')} <span className="text-text-1">{lastCheckinTime ?? 'NA'}</span>
                  </div>
                </div>
              </SurfaceCard>
            )}

            {/* ── SECTION 2: ASSIGNED DISPATCH WORKLOAD ── */}
            <div className="flex flex-col gap-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-md font-black font-space tracking-tight text-text-1 uppercase">
                    {t('officer.active_dispatches', 'Active Dispatches (')}{workload.length})
                  </h3>
                  <p className="text-[10px] font-bold text-text-3 uppercase tracking-wider mt-0.5">
                    {t('officer.tickets_assigned_desc', 'Tickets assigned to your response unit')}
                  </p>
                </div>
                <button
                  onClick={loadOfficerData}
                  className="rounded-lg border border-border px-3 py-1.5 text-[9px] font-black uppercase tracking-wider text-text-2 hover:text-white transition"
                >
                  {t('officer.sync_grid', 'Sync Grid')}
                </button>
              </div>

              {/* Workload Grid */}
              <div className="grid gap-4">
                {workload.map((issue) => (
                  <div
                    key={issue.uuid}
                    onClick={() => setSelectedIssue(issue)}
                    className="group rounded-2xl border border-white/5 bg-surface-1 hover:bg-surface-2 hover:border-brand/30 transition-all p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4 cursor-pointer relative overflow-hidden"
                  >
                    {/* Left glow */}
                    <div className="absolute left-0 top-0 bottom-0 w-1 bg-gradient-to-b from-brand to-brand-light opacity-0 group-hover:opacity-100 transition-opacity" />

                    <div className="flex items-start gap-4 flex-1">
                      {/* Ticket Type Graphic */}
                      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-surface-2 dark:bg-slate-900 border border-white/5 text-brand">
                        <FileText size={18} />
                      </div>

                      <div className="space-y-1">
                        <div className="flex flex-wrap items-center gap-2">
                          <span className={`inline-flex items-center gap-1.5 rounded-full border px-2 py-0.5 text-[9px] font-black uppercase tracking-wider ${getCategoryColor(issue.category)}`}>
                            {issue.category}
                          </span>
                          <span className={`rounded px-1.5 py-0.5 text-[9px] font-semibold uppercase tracking-wider ${getSeverityBadge(issue.severity)}`}>
                            {t('officer.lvl_prefix', 'Lvl ')} {issue.severity}
                          </span>
                          {issue.confirmation_count > 0 && (
                            <span className="rounded bg-surface-2 dark:bg-slate-900 border border-border px-1.5 py-0.5 text-[9px] font-semibold uppercase tracking-wider text-text-3 flex items-center gap-1">
                              <ThumbsUp size={10} /> {issue.confirmation_count} {t('officer.upvotes', 'upvotes')}
                            </span>
                          )}
                        </div>

                        <h4 className="text-sm font-bold text-text-1 uppercase font-space tracking-tight">
                          {issue.issue_type.replace('_', ' ')}
                        </h4>
                        
                        <p className="text-xs text-text-2 line-clamp-1">
                          {issue.description || 'No additional dispatcher notes provided.'}
                        </p>

                        <div className="flex flex-wrap items-center gap-3 text-[10px] font-bold text-text-3 uppercase tracking-wider pt-1">
                          <span className="flex items-center gap-1 text-cyan-400">
                            <MapPin size={10} /> {issue.road_name ?? 'Local Road'}
                          </span>
                          <span>·</span>
                          <span className="flex items-center gap-1">
                            <Clock size={10} /> {getSlaCountdown(issue.sla_deadline)}
                          </span>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center justify-between sm:justify-end gap-3 pt-3 sm:pt-0 border-t border-border/10 sm:border-none">
                      <span className="text-[9px] font-black uppercase tracking-widest text-brand-light group-hover:translate-x-1 transition-transform flex items-center gap-1">
                        {t('officer.respond_action', 'Respond ')} <ChevronRight size={12} />
                      </span>
                    </div>
                  </div>
                ))}

                {workload.length === 0 && (
                  <div className="rounded-2xl border border-white/5 bg-surface-1 p-10 text-center flex flex-col items-center justify-center gap-3">
                    <div className="h-10 w-10 rounded-full bg-emerald-500/10 flex items-center justify-center text-emerald-400 border border-emerald-500/20">
                      <CheckCircle2 size={20} />
                    </div>
                    <div>
                      <h4 className="text-sm font-bold text-text-1 uppercase font-space tracking-tight">{t('officer.grid_secured', 'GRID IS ENTIRELY SECURED')}</h4>
                      <p className="text-[10px] font-bold text-text-3 uppercase tracking-wider mt-1">
                        {t('officer.no_pending_dispatches_desc', 'No pending dispatches on your network. Good job!')}
                      </p>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </>
        )}

        {/* ── SECTION 3: DETAIL / RESOLUTION DRAWER OVERLAY ── */}
        {selectedIssue && (
          <div
            role="dialog"
            aria-modal="true"
            aria-label={`Issue details: ${selectedIssue.issue_type.replace('_', ' ')}`}
            className="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-black/40 dark:bg-slate-950/80 p-0 sm:p-4 backdrop-blur-sm"
          >
            <div className="w-full max-w-lg rounded-t-3xl sm:rounded-3xl border border-white/10 bg-surface-1 dark:bg-slate-950 shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
              {/* Drawer Accent Line */}
              <div className="h-1.5 w-full bg-gradient-to-r from-brand via-brand-light to-brand" />

              {/* Header */}
              <div className="p-6 border-b border-border/20 flex items-start justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <span className={`inline-flex items-center gap-1.5 rounded-full border px-2 py-0.5 text-[9px] font-black uppercase tracking-wider ${getCategoryColor(selectedIssue.category)}`}>
                      {selectedIssue.category}
                    </span>
                    <span className="text-[10px] font-bold text-text-3 uppercase font-mono">
                      {t('officer.ref_prefix', 'Ref: RS-')}{selectedIssue.uuid.slice(0, 8).toUpperCase()}
                    </span>
                  </div>
                  <h3 className="text-lg font-black font-space tracking-tight text-text-1 uppercase mt-2">
                    {selectedIssue.issue_type.replace('_', ' ')}
                  </h3>
                </div>
                <button
                  onClick={() => {
                    setSelectedIssue(null);
                    setResPhoto(null);
                    setPhotoPreview(null);
                    setResNotes('');
                    setErrorMsg(null);
                  }}
                  aria-label="Close issue details"
                  className="rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 p-1.5 text-xs text-text-3 hover:text-white transition"
                >
                  ✕ Close
                </button>
              </div>

              {/* Scrollable details */}
              <div className="p-6 overflow-y-auto space-y-5 flex-1 max-h-[50vh]">
                {/* Details list */}
                <div className="grid grid-cols-2 gap-4 text-xs">
                  <div>
                    <span className="text-[9px] font-bold uppercase tracking-wider text-text-3 block">{t('officer.road_asset', 'Road Asset')}</span>
                    <span className="text-text-1 font-semibold block mt-0.5">
                      {selectedIssue.road_name ?? 'Urban Link'} {selectedIssue.road_number ? `(${selectedIssue.road_number})` : ''}
                    </span>
                  </div>
                  <div>
                    <span className="text-[9px] font-bold uppercase tracking-wider text-text-3 block">{t('officer.geofence_ward', 'Geofence Ward')}</span>
                    <span className="text-text-1 font-semibold block mt-0.5">{selectedIssue.ward_name ?? 'Chennai GCC Zone'}</span>
                  </div>
                  <div>
                    <span className="text-[9px] font-bold uppercase tracking-wider text-text-3 block">{t('officer.sla_target_time', 'SLA Target Time')}</span>
                    <span className="text-text-1 font-semibold block mt-0.5">
                      {selectedIssue.sla_deadline ? new Date(selectedIssue.sla_deadline).toLocaleString('en-IN') : 'None'}
                    </span>
                  </div>
                  <div>
                    <span className="text-[9px] font-bold uppercase tracking-wider text-text-3 block">{t('officer.complaint_date', 'Complaint Date')}</span>
                    <span className="text-text-1 font-semibold block mt-0.5">
                      {new Date(selectedIssue.created_at).toLocaleString('en-IN')}
                    </span>
                  </div>
                </div>

                <div className="rounded-xl border border-white/5 bg-surface-2 dark:bg-slate-900 p-4">
                  <span className="text-[9px] font-bold uppercase tracking-wider text-text-3 block mb-1">{t('officer.citizen_report_details', 'Citizen Report Details')}</span>
                  <p className="text-xs leading-relaxed text-text-2">
                    {selectedIssue.description || t('officer.no_dispatcher_comments', 'No additional dispatcher comments.')}
                  </p>
                </div>

                {/* Evidence Image */}
                {selectedIssue.before_photo_url && (
                  <div>
                    <span className="text-[9px] font-bold uppercase tracking-wider text-text-3 block mb-2">{t('officer.attached_evidence', 'Attached Citizen Evidence')}</span>
                    <div className="relative w-full h-44 rounded-xl overflow-hidden bg-surface-2 dark:bg-slate-900 border border-border/20">
                      <Image
                        src={selectedIssue.before_photo_url}
                        alt="Before evidence"
                        fill
                        unoptimized
                        className="object-cover"
                      />
                    </div>
                  </div>
                )}

                {/* Quick actions (Nav) */}
                <div className="flex gap-3">
                  <button
                    onClick={() => openNavigation(selectedIssue.lat, selectedIssue.lon)}
                    className="flex-1 flex items-center justify-center gap-2 rounded-xl bg-cyan-500/10 hover:bg-cyan-500/20 border border-cyan-500/20 text-cyan-400 py-3 text-xs font-bold uppercase tracking-widest transition"
                  >
                    <Navigation size={14} />
                    <span>{t('officer.navigate_gps', 'Navigate GPS')}</span>
                  </button>
                </div>

                {/* ── RESOLVE FORM INLAY ── */}
                <form onSubmit={handleResolve} className="border-t border-border/20 pt-5 space-y-4">
                  <div>
                    <h4 className="text-sm font-black font-space tracking-tight text-text-1 uppercase">
                      {t('officer.submit_resolution_evidence', 'Submit Resolution Evidence')}
                    </h4>
                    <p className="text-[10px] font-bold text-text-3 uppercase tracking-wider mt-0.5">
                      {t('officer.submit_evidence_hint', 'Submit photographic confirmation of the patch repair to base station.')}
                    </p>
                  </div>

                  {/* Camera Upload */}
                  <div className="flex flex-col items-center justify-center">
                    {photoPreview ? (
                      <div className="relative w-full h-48 rounded-xl overflow-hidden bg-surface-2 dark:bg-slate-900 border border-emerald-500/30 p-2">
                        <div className="relative w-full h-full rounded-lg overflow-hidden">
                          <Image src={photoPreview} alt="Preview" fill className="object-cover" />
                        </div>
                        <button
                          type="button"
                          onClick={() => { setResPhoto(null); setPhotoPreview(null); }}
                          className="absolute right-4 top-4 bg-black/40 dark:bg-slate-950/80 border border-white/10 hover:bg-black/50 dark:hover:bg-slate-950 text-white rounded-lg p-1.5 text-xs transition"
                        >
                          ✕ Retake
                        </button>
                      </div>
                    ) : (
                      <label className="w-full h-32 flex flex-col items-center justify-center gap-2 rounded-xl border border-dashed border-border hover:border-brand/40 bg-surface-2 dark:bg-slate-900 cursor-pointer transition">
                        <Camera size={28} className="text-text-3" />
                        <span className="text-[10px] font-bold uppercase tracking-wider text-text-3">{t('officer.capture_evidence', 'Capture Repair Evidence')}</span>
                        <input
                          type="file"
                          accept="image/*"
                          capture="environment"
                          onChange={handlePhotoChange}
                          className="hidden"
                          required
                        />
                      </label>
                    )}
                  </div>

                  {/* Dispatch Notes */}
                  <div className="flex flex-col gap-1.5">
                    <label className="text-[9px] font-semibold text-text-3 uppercase tracking-[0.25em] pl-1">
                      {t('officer.field_resolution_notes', 'Field Resolution Notes')}
                    </label>
                    <textarea
                      value={resNotes}
                      onChange={e => setResNotes(e.target.value)}
                      placeholder="e.g. Completed pothole sealing using rapid asphalt patch..."
                      rows={3}
                      className="w-full p-4 rounded-xl bg-white/5 dark:bg-white/5 border border-white/10 dark:border-white/10 text-text-1 dark:text-white placeholder:text-text-3 text-xs focus:outline-none focus:border-brand focus:ring-1 focus:ring-brand/40 transition-all resize-none"
                      required
                    />
                  </div>

                  {/* Submission buttons */}
                  <button
                    type="submit"
                    disabled={resolving || !resPhoto}
                    className="w-full h-12 rounded-xl bg-brand hover:bg-[#145230] disabled:opacity-50 disabled:cursor-not-allowed text-white text-xs font-black uppercase tracking-widest shadow-lg shadow-brand/20 transition flex items-center justify-center gap-2"
                  >
                    {resolving ? (
                      <>
                        <Loader2 size={14} className="animate-spin" />
                        <span>{t('officer.broadcasting_base', 'Broadcasting to command center...')}</span>
                      </>
                    ) : (
                      <>
                        <CheckCircle2 size={14} />
                        <span>{t('officer.publish_resolution', 'Publish Ticket Resolution')}</span>
                      </>
                    )}
                  </button>
                </form>
              </div>
            </div>
          </div>
        )}

      </main>
    </div>
  );
}
