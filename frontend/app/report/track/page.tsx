// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
import React from 'react';

'use client';

import { useEffect, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import Link from 'next/link';
import Image from 'next/image';
import {
  MapPin,
  AlertTriangle,
  Clock,
  ArrowLeft,
  ThumbsUp,
  Image as ImageIcon,
  Activity,
  User,
  Info,
} from 'lucide-react';

import { TerminalHeader } from '@/components/ui/TerminalHeader';
import { SurfaceCard } from '@/components/ui/SurfaceCard';
import { client, type RoadIssue } from '@/lib/api';

interface ComplaintEvent {
  id: number;
  event_type: string;
  actor_role?: string | null;
  notes?: string | null;
  created_at: string;
}

interface ComplaintDetails {
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
  ward_name?: string | null;
  sla_deadline?: string | null;
  resolved_at?: string | null;
  duplicate_of_uuid?: string | null;
  confirmation_count: number;
  before_photo_url?: string | null;
  after_photo_url?: string | null;
}

export default function TrackPage() {
  const searchParams = useSearchParams();

  const initialRef = searchParams.get('ref') || '';

  const [refInput, setRefInput] = useState(initialRef);
  const [complaint, setComplaint] = useState<ComplaintDetails | null>(null);
  const [timeline, setTimeline] = useState<ComplaintEvent[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [confirming, setConfirming] = useState(false);
  const [confirmSuccess, setConfirmSuccess] = useState(false);

  async function fetchDetails(ref: string) {
    if (!ref.trim()) return;
    setLoading(true);
    setError(null);
    setConfirmSuccess(false);

    try {
      // Clean query input if they paste RS- prefix or raw uuid
      let identifier = ref.trim();
      
      // If it's a reference e.g. RS-XXXX, search by ref, else assume UUID
      let issueUuid = identifier;
      if (identifier.startsWith('RS-')) {
        // Query paginated issues and filter by complaint_ref
        const { data } = await client.get(`/api/v1/roads/issues?radius=50000&limit=1&lat=13.08&lon=80.27`);
        const found = data.issues?.find((i: RoadIssue) => i.uuid.toUpperCase().includes(identifier.replace('RS-', '').toUpperCase()));
        if (found) {
          issueUuid = found.uuid;
        } else {
          // Fallback search in all admin complaints
          const adminRes = await client.get('/api/v1/admin/complaints', { params: { limit: 100 } });
          const adminFound = adminRes.data.issues?.find((i: RoadIssue) => i.uuid.toUpperCase().includes(identifier.replace('RS-', '').toUpperCase()));
          if (adminFound) {
            issueUuid = adminFound.uuid;
          } else {
            throw new Error("Complaint reference not found.");
          }
        }
      }

      // 1. Fetch details
      const detailRes = await client.get(`/api/v1/roads/issues/${issueUuid}`);
      setComplaint(detailRes.data);

      // 2. Fetch timeline
      const timelineRes = await client.get(`/api/v1/roads/issues/${issueUuid}/timeline`);
      setTimeline(timelineRes.data.timeline || []);

      // Update URL query param silently
      const url = new URL(window.location.href);
      url.searchParams.set('ref', ref);
      window.history.replaceState({}, '', url.toString());

    } catch (err: unknown) {
      setComplaint(null);
      setTimeline([]);
      const axiosErr = err as { response?: { data?: { detail?: string } }; message?: string };
      setError(axiosErr.response?.data?.detail || axiosErr.message || "Failed to load complaint. Please verify your reference ID.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (initialRef) {
      fetchDetails(initialRef);
    }
  }, [initialRef]);

  async function handleConfirm() {
    if (!complaint) return;
    setConfirming(true);
    try {
      const { data } = await client.post(`/api/v1/roads/report/${complaint.uuid}/confirm`);
      setComplaint(prev => prev ? { ...prev, confirmation_count: data.confirmations, status: data.complaint_status } : null);
      setConfirmSuccess(true);
      // Re-fetch timeline
      const timelineRes = await client.get(`/api/v1/roads/issues/${complaint.uuid}/timeline`);
      setTimeline(timelineRes.data.timeline || []);
    } catch (err: unknown) {
      console.error(err);
    } finally {
      setConfirming(false);
    }
  }

  function getStatusLabel(status: string) {
    switch (status) {
      case 'open': return 'Reported';
      case 'acknowledged': return 'Acknowledged';
      case 'in_progress': return 'Work In Progress';
      case 'resolved': return 'Resolved';
      case 'rejected': return 'Rejected';
      default: return status;
    }
  }

  function getStatusColor(status: string) {
    switch (status) {
      case 'open': return 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20';
      case 'acknowledged': return 'bg-blue-500/10 text-blue-400 border-blue-500/20';
      case 'in_progress': return 'bg-amber-500/10 text-amber-400 border-amber-500/20';
      case 'resolved': return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20';
      case 'rejected': return 'bg-red-500/10 text-red-400 border-red-500/20';
      default: return 'bg-slate-500/10 text-slate-400 border-slate-500/20';
    }
  }

  // Calculate SLA countdown
  const slaRemaining = () => {
    if (!complaint?.sla_deadline || complaint.status === 'resolved' || complaint.status === 'rejected') return null;
    const diff = new Date(complaint.sla_deadline).getTime() - Date.now();
    if (diff <= 0) return 'Breached';
    
    const hours = Math.floor(diff / (1000 * 60 * 60));
    const mins = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
    return `${hours}h ${mins}m remaining`;
  };

  return (
    <div className="sv-page sv-aurora relative min-h-screen bg-surface-1 dark:bg-slate-950 text-text-1 dark:text-slate-100 pb-20">
      <h1 className="sr-only">Complaint Tracker</h1>
      <div className="pointer-events-none absolute inset-0 z-0 overflow-hidden">
        <div className="absolute right-[-10%] top-[-12%] h-[38rem] w-[38rem] rounded-full bg-cyan-500/5 blur-[150px]" />
        <div className="absolute left-[-8%] bottom-[-16%] h-[28rem] w-[28rem] rounded-full bg-brand/5 blur-[140px]" />
      </div>

      <TerminalHeader title="Complaint Tracker Uplink" subtitle="MONITOR RESOLUTION TIMELINES" />

      <main className="relative z-10 mx-auto flex w-full max-w-4xl flex-col gap-6 px-4 pt-28 sm:px-6">
        
        {/* Navigation back */}
        <Link href="/report" className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-text-3 hover:text-brand-light transition w-fit">
          <ArrowLeft size={14} /> Back to Sentinel Report Form
        </Link>

        {/* Ref Search Bar */}
        <SurfaceCard>
          <div className="text-[10px] font-semibold uppercase tracking-[0.22em] text-text-3">Track Complaint</div>
          <h2 className="mt-1 text-xl font-black font-space tracking-tight text-text-1">ENTER REFERENCE ID OR UUID</h2>
          
          <form
            onSubmit={(e) => { e.preventDefault(); fetchDetails(refInput); }}
            className="mt-4 flex flex-col gap-3 sm:flex-row"
          >
            <input
              type="text"
              value={refInput}
              onChange={(e) => setRefInput(e.target.value)}
              placeholder="e.g. RS-D38E1FC5B1 or UUID"
              aria-label="Reference ID or UUID"
              className="flex-1 rounded-[1.5rem] border border-border bg-surface-2 px-5 py-4 text-sm font-semibold uppercase tracking-wider text-text-1 outline-none transition placeholder:text-text-3 focus:border-brand/40 focus:bg-surface-3"
            />
            <button
              type="submit"
              disabled={loading || !refInput.trim()}
              className="rounded-[1.6rem] bg-brand hover:bg-brand-light px-8 py-4 text-xs font-bold uppercase tracking-widest text-white shadow-lg shadow-brand/20 transition disabled:opacity-50"
            >
              {loading ? 'Uplinking...' : 'Locate Report'}
            </button>
          </form>

          {error && (
            <div className="mt-4 rounded-lg border border-red-500/20 bg-red-500/10 px-4 py-3 text-sm font-semibold text-red-400 flex items-center gap-3">
              <AlertTriangle size={18} className="flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}
        </SurfaceCard>

        {/* Details Screen */}
        {complaint && (
          <div className="grid gap-6">
            
            {/* Top row status */}
            <div className="grid gap-6 md:grid-cols-3">
              <SurfaceCard className="flex flex-col justify-between">
                <div>
                  <div className="text-[10px] font-semibold uppercase tracking-[0.22em] text-text-3">STATUS LOCK</div>
                  <div className={`mt-3 inline-flex items-center gap-2 rounded-full border px-3 py-1.5 text-xs font-bold uppercase tracking-widest ${getStatusColor(complaint.status)}`}>
                    <Activity size={12} className="animate-pulse" />
                    {getStatusLabel(complaint.status)}
                  </div>
                </div>
                <p className="mt-3 text-xs text-text-3 uppercase tracking-wider">
                  Reported: {new Date(complaint.created_at).toLocaleDateString('en-IN', { dateStyle: 'medium' })}
                </p>
              </SurfaceCard>

              <SurfaceCard className="flex flex-col justify-between">
                <div>
                  <div className="text-[10px] font-semibold uppercase tracking-[0.22em] text-text-3">WARD Geofence</div>
                  <div className="mt-3 text-lg font-black text-text-1 uppercase tracking-tight">{complaint.ward_name ?? 'Chennai Outer Ring'}</div>
                </div>
                <div className="mt-3 flex items-center gap-2 text-xs text-text-3">
                  <MapPin size={12} /> GCC Municipal Geofenced Zone
                </div>
              </SurfaceCard>

              <SurfaceCard className="flex flex-col justify-between">
                <div>
                  <div className="text-[10px] font-semibold uppercase tracking-[0.22em] text-text-3">SLA TIMELINE</div>
                  <div className="mt-3 text-lg font-black text-text-1 uppercase tracking-tight flex items-center gap-2">
                    <Clock size={16} className="text-brand-light" />
                    {slaRemaining() ?? 'Resolved / Met'}
                  </div>
                </div>
                <p className="mt-3 text-xs text-text-3 uppercase tracking-wider">
                  SLA Target: {complaint.sla_deadline ? new Date(complaint.sla_deadline).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' }) : 'NA'}
                </p>
              </SurfaceCard>
            </div>

            {/* Evidence comparison */}
            <SurfaceCard>
              <div className="text-[10px] font-semibold uppercase tracking-[0.22em] text-text-3">Evidence Locker</div>
              <h2 className="mt-1 text-xl font-black font-space tracking-tight text-text-1 uppercase">BEFORE & AFTER RESOLUTION PHOTOS</h2>
              
              <div className="mt-5 grid gap-4 sm:grid-cols-2">
                {/* Before Photo */}
                <div className="rounded-[1.5rem] border border-border bg-surface-2 p-3 overflow-hidden flex flex-col justify-between min-h-[260px]">
                  <div className="relative w-full h-[200px] rounded-lg overflow-hidden bg-surface-2 dark:bg-slate-900 flex items-center justify-center">
                    {complaint.before_photo_url ? (
                      <Image
                        src={complaint.before_photo_url}
                        alt="Before evidence"
                        fill
                        unoptimized
                        className="object-cover"
                      />
                    ) : (
                      <div className="flex flex-col items-center gap-2 text-text-3">
                        <ImageIcon size={32} />
                        <span className="text-xs font-semibold uppercase tracking-wider">No photo attached by citizen</span>
                      </div>
                    )}
                  </div>
                  <div className="mt-3 text-center text-xs font-semibold uppercase tracking-wider text-cyan-400">🚨 BEFORE UPLINK EVIDENCE</div>
                </div>

                {/* After Photo */}
                <div className="rounded-[1.5rem] border border-border bg-surface-2 p-3 overflow-hidden flex flex-col justify-between min-h-[260px]">
                  <div className="relative w-full h-[200px] rounded-lg overflow-hidden bg-surface-2 dark:bg-slate-900 flex items-center justify-center">
                    {complaint.after_photo_url ? (
                      <Image
                        src={complaint.after_photo_url}
                        alt="After evidence"
                        fill
                        unoptimized
                        className="object-cover"
                      />
                    ) : (
                      <div className="flex flex-col items-center gap-2 text-text-3">
                        <ImageIcon size={32} className="animate-pulse" />
                        <span className="text-xs font-semibold uppercase tracking-wider">Resolution evidence pending</span>
                      </div>
                    )}
                  </div>
                  <div className="mt-3 text-center text-xs font-semibold uppercase tracking-wider text-emerald-400">✅ AFTER REPAIR EVIDENCE</div>
                </div>
              </div>
            </SurfaceCard>

            {/* Upvote & Description Panel */}
            <div className="grid gap-6 md:grid-cols-3">
              <SurfaceCard className="md:col-span-2">
                <div className="text-[10px] font-semibold uppercase tracking-[0.22em] text-text-3">DISPATCH NOTES</div>
                <h3 className="mt-1 text-lg font-black text-text-1 uppercase font-space">{complaint.issue_type}</h3>
                <p className="mt-3 text-sm leading-6 text-text-2">{complaint.description || "No descriptive notes supplied by reporter."}</p>
                
                <div className="mt-5 border-t border-border pt-4 grid grid-cols-2 gap-3">
                  <div>
                    <div className="text-[9px] font-semibold uppercase tracking-wider text-text-3">ROAD NETWORK</div>
                    <div className="text-xs font-bold text-text-1 mt-1">{complaint.road_name || 'Urban Link'} ({complaint.road_type || 'Local Road'})</div>
                  </div>
                  <div>
                    <div className="text-[9px] font-semibold uppercase tracking-wider text-text-3">OWNERSHIP DEP</div>
                    <div className="text-xs font-bold text-text-1 mt-1">{complaint.authority_name || 'Municipal Corp'}</div>
                  </div>
                </div>
              </SurfaceCard>

              <SurfaceCard className="flex flex-col justify-between items-center text-center">
                <div>
                  <div className="text-[10px] font-semibold uppercase tracking-[0.22em] text-text-3">UPVOTE CONFIRMATION</div>
                  <div className="mt-4 text-3xl font-black text-brand-light">{complaint.confirmation_count}</div>
                  <p className="mt-2 text-xs text-text-3 leading-relaxed">
                    Upvoting verifies report legitimacy and escalates authority urgency.
                  </p>
                </div>

                <button
                  type="button"
                  onClick={handleConfirm}
                  disabled={confirming || confirmSuccess || complaint.status === 'resolved'}
                  className="mt-4 w-full inline-flex items-center justify-center gap-2 rounded-xl bg-brand/10 hover:bg-brand/20 border border-brand/20 text-brand-light px-4 py-3 text-xs font-bold uppercase tracking-widest transition disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <ThumbsUp size={14} className={confirming ? "animate-spin" : ""} />
                  {confirmSuccess ? 'Confirmed!' : 'Upvote Ticket'}
                </button>
              </SurfaceCard>
            </div>

            {/* Stepper Timeline Log */}
            <SurfaceCard>
              <div className="text-[10px] font-semibold uppercase tracking-[0.22em] text-text-3">AUDIT TRAIL LOG</div>
              <h2 className="mt-1 text-xl font-black font-space tracking-tight text-text-1 uppercase">COMPLAINT LIFECYCLE TIMELINE</h2>
              
              <div className="mt-8 relative border-l-2 border-border ml-4 pl-6 space-y-8">
                {timeline.map((event) => (
                  <div key={event.id} className="relative">
                    {/* Step bubble icon */}
                    <div className="absolute left-[-32px] top-[2px] h-4 w-4 rounded-full border-2 border-brand bg-surface-1 dark:bg-slate-950 flex items-center justify-center">
                      <div className="h-1.5 w-1.5 rounded-full bg-brand-light animate-ping" />
                    </div>

                    <div>
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="text-xs font-black uppercase tracking-wider text-text-1">
                          {event.event_type.toUpperCase()}
                        </span>
                        {event.actor_role && (
                          <span className="rounded bg-surface-3 dark:bg-slate-800 px-1.5 py-0.5 text-[9px] font-semibold uppercase tracking-wider text-text-3 flex items-center gap-1">
                            <User size={10} /> {event.actor_role}
                          </span>
                        )}
                        <span className="text-[10px] text-text-3 font-semibold tracking-wider">
                          {new Date(event.created_at).toLocaleString('en-IN', { dateStyle: 'short', timeStyle: 'short' })}
                        </span>
                      </div>
                      <p className="mt-2 text-xs font-medium text-text-2 leading-relaxed bg-surface-2 border border-border/10 rounded-xl px-4 py-2.5 w-fit max-w-lg">
                        {event.notes}
                      </p>
                    </div>
                  </div>
                ))}

                {timeline.length === 0 && (
                  <div className="text-sm font-semibold text-text-3 py-2 flex items-center gap-2">
                    <Info size={16} /> Generating live audit log feed...
                  </div>
                )}
              </div>
            </SurfaceCard>

          </div>
        )}

      </main>
    </div>
  );
}
