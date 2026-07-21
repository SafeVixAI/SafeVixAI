'use client';

// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
import React from 'react';


import { useEffect, useState, useMemo, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import dynamic from 'next/dynamic';
import {
  Loader2,
  AlertTriangle,
  UserCheck,
  MapPin,
  CheckCircle,
  Activity,
  Clock,
  Search,
  X,
  Navigation,
  TrafficCone,
  Lightbulb,
} from 'lucide-react';

import { TerminalHeader } from '@/components/ui/TerminalHeader';
import { SurfaceCard } from '@/components/ui/SurfaceCard';
import { client } from '@/lib/api';
import { sounds } from '@/lib/sounds';

const MapLibreLoader = () => {
  const { t } = useTranslation('common');
  return (
    <div className="w-full h-[380px] bg-surface-2 dark:bg-slate-900 rounded-[1.8rem] flex items-center justify-center border border-border">
      <div className="flex flex-col items-center gap-3">
        <Loader2 size={32} className="animate-spin text-brand" />
        <span className="text-xs font-semibold uppercase tracking-widest text-text-3">{t('dashboard.gis_warming', 'Warming GIS Engines...')}</span>
      </div>
    </div>
  );
};

// Dynamically import MapLibre Component to disable SSR
const MapLibreDashboard = dynamic(() => import('@/components/command-center/MapLibreDashboard'), {
  ssr: false,
  loading: MapLibreLoader,
});

interface KPI {
  active_complaints: number;
  resolved_complaints: number;
  total_complaints: number;
  sla_breaches: number;
  active_field_officers: number;
  overall_resolution_rate: number;
}

interface Officer {
  id: string;
  name: string;
  department: string;
  role: string;
  is_active: boolean;
  ward_id: string;
  last_checkin?: string | null;
}

interface Complaint {
  uuid: string;
  complaint_ref: string;
  issue_type: string;
  severity: number;
  description: string;
  location_address: string;
  status: string;
  created_at: string;
  category: string;
  ward_name: string;
  assigned_officer_id?: string | null;
  sla_deadline?: string | null;
}

interface WardSummary {
  ward_id: string;
  ward_name: string;
  zone_name: string;
  open_issues: number;
  resolved_issues: number;
  resolution_rate: number;
  sla_breach_count: number;
}

export default function CommandCenterPage() {
  const { t } = useTranslation('common');
  const [mounted, setMounted] = useState(false);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [kpis, setKpis] = useState<KPI | null>(null);
  const [categories, setCategories] = useState<Record<string, number>>({ roads: 0, traffic: 0, streetlight: 0 });
  const [complaints, setComplaints] = useState<Complaint[]>([]);
  const [officers, setOfficers] = useState<Officer[]>([]);
  const [wards, setWards] = useState<WardSummary[]>([]);
  const [breaches, setBreaches] = useState<Complaint[]>([]);
  const knownSev5Ids = useRef<Set<string>>(new Set());
  
  // Selection states for assignment modal/inline
  const [assigningUuid, setAssigningUuid] = useState<string | null>(null);
  const [selectedOfficerId, setSelectedOfficerId] = useState<string>('');
  const [actionLoading, setActionLoading] = useState(false);

  // Enterprise: Search, Filter, Detail Panel
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [selectedComplaint, setSelectedComplaint] = useState<Complaint | null>(null);

  // Status filter tabs
  const STATUS_TABS = [
    { key: 'all', label: 'All' },
    { key: 'open', label: 'Open' },
    { key: 'acknowledged', label: 'Assigned' },
    { key: 'in_progress', label: 'In Progress' },
    { key: 'resolved', label: 'Resolved' },
  ];

  // Time ago helper
  function timeAgo(dateStr: string): string {
    if (!dateStr) return 'Unknown';
    const now = Date.now();
    const then = new Date(dateStr).getTime();
    if (isNaN(then)) return 'Invalid date';
    const diffMs = now - then;
    const mins = Math.floor(diffMs / 60000);
    if (mins < 1) return 'Just now';
    if (mins < 60) return `${mins}m ago`;
    const hrs = Math.floor(mins / 60);
    if (hrs < 24) return `${hrs}h ago`;
    const days = Math.floor(hrs / 24);
    if (days === 1) return 'Yesterday';
    if (days < 7) return `${days}d ago`;
    return new Date(dateStr).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' });
  }

  // Filtered complaints
  const filteredComplaints = useMemo(() => {
    let result = complaints;
    if (statusFilter !== 'all') {
      result = result.filter((c) => c.status === statusFilter);
    }
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      result = result.filter(
        (c) =>
          (c.location_address || '').toLowerCase().includes(q) ||
          (c.category || '').toLowerCase().includes(q) ||
          (c.issue_type || '').toLowerCase().includes(q) ||
          (c.ward_name || '').toLowerCase().includes(q) ||
          (c.complaint_ref || '').toLowerCase().includes(q)
      );
    }
    return result;
  }, [complaints, statusFilter, searchQuery]);

  // Status counts
  const statusCounts = useMemo(() => {
    const counts = new Map<string, number>([['all', complaints.length]]);
    for (const c of complaints) {
      counts.set(c.status, (counts.get(c.status) ?? 0) + 1);
    }
    return counts;
  }, [complaints]);

  async function loadDashboardData() {
    try {
      // 1. Fetch Overall Stats (Admin Dashboard)
      const statsRes = await client.get('/api/v1/admin/dashboard');
      setKpis(statsRes.data.kpis);
      setCategories(statsRes.data.category_breakdown);

      // 2. Fetch Open Complaints
      const complaintsRes = await client.get('/api/v1/admin/complaints', { params: { limit: 50 } });
      const newComplaints = complaintsRes.data.issues || [];
      setComplaints(newComplaints);

      // Detect new Sev 5 incidents
      let hasNewSev5 = false;
      const currentSev5Ids = new Set<string>();
      newComplaints.forEach((c: Complaint) => {
        if (c.severity === 5) {
          currentSev5Ids.add(c.uuid);
          if (knownSev5Ids.current.size > 0 && !knownSev5Ids.current.has(c.uuid)) {
            hasNewSev5 = true;
          }
        }
      });
      knownSev5Ids.current = currentSev5Ids;
      if (hasNewSev5) {
        sounds.sev5Alert();
      }

      // 3. Fetch Officers
      const officersRes = await client.get('/api/v1/admin/officers');
      setOfficers(officersRes.data || []);

      // 4. Fetch Ward Summaries
      const wardsRes = await client.get('/api/v1/analytics/ward-summary');
      setWards(wardsRes.data || []);

      // 5. Fetch SLA Breaches
      const breachesRes = await client.get('/api/v1/analytics/sla-breach');
      setBreaches(breachesRes.data || []);

    } catch (err) {
      console.error("Failed to load command center data:", err);
      setLoadError(err instanceof Error ? err.message : 'Failed to load command center data');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    setMounted(true);
    document.title = 'Command Center | SafeVixAI';
    loadDashboardData();
    // Refresh every 30 seconds for live feel
    const interval = setInterval(loadDashboardData, 30000);
    return () => clearInterval(interval);
  }, []);

  async function handleAssign(issueUuid: string) {
    if (!selectedOfficerId) return;
    setActionLoading(true);
    try {
      await client.post(`/api/v1/admin/complaints/${issueUuid}/assign`, null, {
        params: { officer_id: selectedOfficerId },
      });
      setAssigningUuid(null);
      setSelectedOfficerId('');
      // Reload dashboard KPIs and lists
      await loadDashboardData();
    } catch (err) {
      console.error("Assignment failed:", err);
    } finally {
      setActionLoading(false);
    }
  }

  return (
    <div className={`sv-page sv-aurora relative min-h-screen bg-surface-1 dark:bg-slate-950 text-text-1 dark:text-slate-100 pb-20 ${!mounted ? 'opacity-0' : ''}`}>
      <h1 className="sr-only">Command Center</h1>
      <div className="pointer-events-none absolute inset-0 z-0 overflow-hidden">
        <div className="absolute right-[-10%] top-[-10%] h-[40rem] w-[40rem] rounded-full bg-brand/5 blur-[150px]" />
        <div className="absolute left-[-5%] top-[10%] h-[30rem] w-[30rem] rounded-full bg-cyan-500/5 blur-[130px]" />
      </div>

      <TerminalHeader title="Civic Intelligence Center" subtitle="GCC ROAD WATCH COMMAND SENTINEL" />

      <main className="relative z-10 mx-auto flex w-full max-w-7xl flex-col gap-6 px-4 pt-28 sm:px-6">
        
        {loading ? (
          <div className="flex h-[60vh] w-full flex-col items-center justify-center gap-4">
            <Loader2 size={42} className="animate-spin text-brand" />
            <div className="text-xs font-black uppercase tracking-[0.2em] text-text-3">{t('dashboard.dispatching_sensors', 'DISPATCHING SENSORS...')}</div>
          </div>
        ) : loadError ? (
          <div className="flex h-[60vh] w-full flex-col items-center justify-center gap-4">
            <AlertTriangle size={42} className="text-red-400" />
            <div className="text-sm font-bold text-red-400">{loadError}</div>
            <button onClick={() => { setLoading(true); setLoadError(null); loadDashboardData(); }} className="px-4 py-2 bg-brand text-white rounded-xl text-xs font-bold uppercase tracking-wider">
              Retry
            </button>
          </div>
        ) : (
          <div className="grid gap-6">
            
            {/* ── KPI Grid ── */}
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <SurfaceCard className="border-cyan-500/20 bg-cyan-950/10">
                <div className="flex items-center justify-between">
                  <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-cyan-400">{t('dashboard.active_incidents', 'ACTIVE INCIDENTS')}</div>
                  <Activity size={16} className="text-cyan-400 animate-pulse" />
                </div>
                <div className="mt-4 text-3xl font-black font-space tracking-tight text-text-1 dark:text-white">{kpis?.active_complaints ?? 0}</div>
                <div className="mt-2 text-[10px] font-semibold text-text-3 uppercase tracking-wider">{t('dashboard.deserving_patrol', 'Deserving Immediate Patrol')}</div>
              </SurfaceCard>

              <SurfaceCard className="border-red-500/20 bg-red-950/10">
                <div className="flex items-center justify-between">
                  <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-red-400">{t('dashboard.sla_breaches', 'SLA BREACHES')}</div>
                  <Clock size={16} className="text-red-400 animate-bounce" />
                </div>
                <div className="mt-4 text-3xl font-black font-space tracking-tight text-text-1 dark:text-white">{kpis?.sla_breaches ?? 0}</div>
                <div className="mt-2 text-[10px] font-semibold text-red-400 uppercase tracking-wider font-semibold animate-pulse">{t('dashboard.needs_escalation', 'Needs Escalation')}</div>
              </SurfaceCard>

              <SurfaceCard className="border-emerald-500/20 bg-emerald-950/10">
                <div className="flex items-center justify-between">
                  <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-emerald-400">{t('dashboard.resolved_tickets', 'RESOLVED TICKETS')}</div>
                  <CheckCircle size={16} className="text-emerald-400" />
                </div>
                <div className="mt-4 text-3xl font-black font-space tracking-tight text-text-1 dark:text-white">{kpis?.resolved_complaints ?? 0}</div>
                <div className="mt-2 text-[10px] font-semibold text-text-3 uppercase tracking-wider">{kpis?.overall_resolution_rate ?? 0}% {t('dashboard.overall_resolution_rate_desc', 'overall resolution rate')}</div>
              </SurfaceCard>

              <SurfaceCard className="border-brand/20 bg-brand/10">
                <div className="flex items-center justify-between">
                  <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-brand-light">{t('dashboard.active_teams', 'ACTIVE TEAMS')}</div>
                  <UserCheck size={16} className="text-brand-light" />
                </div>
                <div className="mt-4 text-3xl font-black font-space tracking-tight text-text-1 dark:text-white">{kpis?.active_field_officers ?? 0}</div>
                <div className="mt-2 text-[10px] font-semibold text-text-3 uppercase tracking-wider">{t('dashboard.gps_tracked_squads', 'GPS tracked field squads')}</div>
              </SurfaceCard>
            </div>

            {/* ── GIS Map and Breakdown Row ── */}
            <div className="grid gap-6 lg:grid-cols-3">
              <div className="lg:col-span-2">
                <SurfaceCard padding="none" className="h-full overflow-hidden">
                  <div className="p-5 border-b border-border">
                    <div className="text-[10px] font-semibold uppercase tracking-[0.22em] text-text-3">{t('dashboard.gcc_live_feeds', 'GCC LIVE FEEDS')}</div>
                    <h2 className="text-lg font-black font-space tracking-tight text-text-1">{t('dashboard.gcc_choropleth_heatmap', 'GCC CHOROPLETH WARD HEATMAP')}</h2>
                  </div>
                  <div className="h-[380px] w-full">
                    <MapLibreDashboard activeCategory="" />
                  </div>
                </SurfaceCard>
              </div>

              {/* Category charts & breaches */}
              <div className="flex flex-col gap-6">
                <SurfaceCard className="flex-1">
                  <div className="text-[10px] font-semibold uppercase tracking-[0.22em] text-text-3">{t('dashboard.category_breakdown', 'Category Breakdown')}</div>
                  <h3 className="mt-1 text-lg font-black font-space tracking-tight text-text-1 uppercase">{t('dashboard.distribution_departments', 'DISTRIBUTION BY DEPARTMENTS')}</h3>
                  
                  <div className="mt-6 space-y-4">
                    {/* Roads */}
                    <div>
                      <div className="flex justify-between text-xs font-bold uppercase tracking-wider text-text-2">
                        <span><Navigation size={14} className="inline mr-1.5 text-cyan-400" />Roads & Bridges</span>
                        <span>{categories.roads}</span>
                      </div>
                      <div className="mt-2 h-2.5 w-full rounded-full bg-surface-3 dark:bg-slate-800 overflow-hidden">
                        <div className="h-full bg-cyan-500 rounded-full" style={{ width: `${(categories.roads / (kpis?.active_complaints || 1)) * 100}%` }} />
                      </div>
                    </div>

                    {/* Traffic */}
                    <div>
                      <div className="flex justify-between text-xs font-bold uppercase tracking-wider text-text-2">
                        <span><TrafficCone size={14} className="inline mr-1.5 text-amber-400" />Traffic & Signage</span>
                        <span>{categories.traffic}</span>
                      </div>
                      <div className="mt-2 h-2.5 w-full rounded-full bg-surface-3 dark:bg-slate-800 overflow-hidden">
                        <div className="h-full bg-amber-500 rounded-full" style={{ width: `${(categories.traffic / (kpis?.active_complaints || 1)) * 100}%` }} />
                      </div>
                    </div>

                    {/* Streetlight */}
                    <div>
                      <div className="flex justify-between text-xs font-bold uppercase tracking-wider text-text-2">
                        <span><Lightbulb size={14} className="inline mr-1.5 text-brand-light" />Public Streetlighting</span>
                        <span>{categories.streetlight}</span>
                      </div>
                      <div className="mt-2 h-2.5 w-full rounded-full bg-surface-3 dark:bg-slate-800 overflow-hidden">
                        <div className="h-full bg-brand-light rounded-full" style={{ width: `${(categories.streetlight / (kpis?.active_complaints || 1)) * 100}%` }} />
                      </div>
                    </div>
                  </div>
                </SurfaceCard>

                {/* SLA Breaches Alerts */}
                <SurfaceCard className="max-h-[220px] overflow-y-auto">
                  <div className="flex items-center gap-2 text-[10px] font-black uppercase tracking-[0.2em] text-red-500">
                    <AlertTriangle size={12} className="animate-pulse" />
                    {t('dashboard.critical_sla_feed', 'CRITICAL SLA BREACH FEED ({{count}})', { count: breaches.length })}
                  </div>
                  
                  <div className="mt-3 divide-y divide-border/10">
                    {breaches.slice(0, 5).map((b) => (
                      <div key={b.uuid} className="py-2.5 flex items-center justify-between gap-3">
                        <div className="min-w-0">
                          <div className="text-xs font-black uppercase tracking-wider text-text-1 dark:text-white truncate">{b.complaint_ref} — {b.issue_type}</div>
                          <div className="text-[10px] text-text-3 mt-0.5 truncate">{b.location_address}</div>
                        </div>
                        <span className="text-[9px] font-bold uppercase tracking-widest text-red-400 bg-red-500/10 border border-red-500/20 px-2 py-0.5 rounded">
                          {t('dashboard.overdue', 'OVERDUE')}
                        </span>
                      </div>
                    ))}
                    {breaches.length === 0 && (
                      <div className="text-xs text-text-3 font-semibold py-4 text-center">{t('dashboard.no_sla_breaches', 'No active SLA breaches! Good response time.')}</div>
                    )}
                  </div>
                </SurfaceCard>
              </div>
            </div>

            {/* ── Active Incident Feed & Live Assignment ── */}
            <div className="grid gap-6 lg:grid-cols-3">
              {/* Incident list */}
              <div className="lg:col-span-2">
                <SurfaceCard>
                  <div className="text-[10px] font-semibold uppercase tracking-[0.22em] text-text-3">{t('dashboard.dispatch_desk', 'Dispatch Desk')}</div>
                  <h2 className="mt-1 text-xl font-black font-space tracking-tight text-text-1 uppercase">{t('dashboard.live_complaint_stream', 'LIVE CITIZEN COMPLAINT STREAM')}</h2>

                  {/* Search Bar */}
                  <div className="mt-4 relative">
                    <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-3" />
                    <input
                      id="cc-search"
                      type="text"
                      placeholder="Search complaints..."
                      aria-label="Search complaints"
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="w-full pl-9 pr-4 py-2.5 bg-surface-2 border border-border rounded-xl text-xs text-text-1 placeholder:text-text-3 focus:outline-none focus:border-brand/50 transition-colors"
                    />
                  </div>

                  {/* Status Filter Tabs */}
                  <div className="mt-3 flex flex-wrap gap-2">
                    {STATUS_TABS.map((tab) => (
                      <button
                        key={tab.key}
                        onClick={() => setStatusFilter(tab.key)}
                        className={`px-3 py-1.5 rounded-lg text-[10px] font-bold uppercase tracking-wider transition-colors ${
                          statusFilter === tab.key
                            ? 'bg-brand text-white'
                            : 'bg-surface-3 text-text-3 hover:text-text-1'
                        }`}
                      >
                        {tab.label}
                        <span className="ml-1.5 px-1.5 py-0.5 rounded bg-black/20 text-[9px]">
                          {statusCounts.get(tab.key) ?? 0}
                        </span>
                      </button>
                    ))}
                  </div>
                  
                  <div className="mt-4 overflow-x-auto">
                    <table className="w-full text-left border-collapse">
                      <thead>
                        <tr className="border-b border-border/20 text-[10px] font-black uppercase tracking-widest text-text-3">
                          <th className="pb-3">{t('dashboard.table.ref_type', 'REF / TYPE')}</th>
                          <th className="pb-3">{t('dashboard.table.location', 'LOCATION')}</th>
                          <th className="pb-3">{t('dashboard.table.severity', 'SEVERITY')}</th>
                          <th className="pb-3">{t('dashboard.table.time', 'TIME')}</th>
                          <th className="pb-3 text-right">{t('dashboard.table.action', 'ACTION')}</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-border/10 text-xs">
                        {filteredComplaints.map((c) => (
                          <tr
                            key={c.uuid}
                            className="hover:bg-surface-2 transition cursor-pointer"
                            onClick={() => setSelectedComplaint(c)}
                          >
                            <td className="py-4 pr-3">
                              <div className="font-black text-text-1 dark:text-white">{c.complaint_ref || c.uuid.slice(0, 8).toUpperCase()}</div>
                              <div className="text-[10px] text-text-3 mt-1 uppercase tracking-wider">{c.category} - {c.issue_type}</div>
                            </td>
                            <td className="py-4 pr-3 max-w-[200px] truncate">
                              <div className="font-semibold text-text-2">{c.location_address || 'Location pending'}</div>
                              <div className="text-[10px] text-text-3 mt-1 uppercase tracking-wider">{c.ward_name}</div>
                            </td>
                            <td className="py-4 pr-3">
                              <span className={`inline-block px-2.5 py-0.5 rounded text-[10px] font-black uppercase tracking-wider ${
                                c.severity >= 4 ? 'bg-red-500/10 text-red-400 border border-red-500/20' : 'bg-brand/10 text-brand-light border border-brand/20'
                              }`}>
                                {t('dashboard.sev_prefix', 'Sev')} {c.severity}
                              </span>
                            </td>
                            <td className="py-4 pr-3">
                              <span className="text-[10px] font-semibold text-text-3">{timeAgo(c.created_at)}</span>
                            </td>
                            <td className="py-4 text-right" onClick={(e) => e.stopPropagation()}>
                              {assigningUuid === c.uuid ? (
                                <div className="inline-flex items-center gap-2">
                                  <select
                                    value={selectedOfficerId}
                                    onChange={(e) => setSelectedOfficerId(e.target.value)}
                                    className="rounded bg-surface-2 dark:bg-slate-900 border border-border text-xs px-2 py-1 outline-none font-semibold"
                                  >
                                    <option value="">{t('dashboard.select_officer', 'Select Officer')}</option>
                                    {officers.map((o) => (
                                      <option key={o.id} value={o.id}>{o.name} ({o.department})</option>
                                    ))}
                                  </select>
                                  <button
                                    onClick={() => handleAssign(c.uuid)}
                                    disabled={actionLoading || !selectedOfficerId}
                                    className="bg-brand text-white text-[10px] font-black px-2.5 py-1 rounded transition hover:bg-brand-light disabled:opacity-50"
                                  >
                                    {t('common:ok', 'OK')}
                                  </button>
                                  <button
                                    onClick={() => setAssigningUuid(null)}
                                    className="bg-surface-3 dark:bg-slate-800 text-text-2 text-[10px] font-black px-2.5 py-1 rounded hover:bg-surface-1 dark:hover:bg-slate-700"
                                  >
                                    {t('common:cancel', 'Cancel')}
                                  </button>
                                </div>
                              ) : (
                                <button
                                  onClick={() => {
                                    setAssigningUuid(c.uuid);
                                    setSelectedOfficerId('');
                                  }}
                                  className={`px-3 py-1.5 rounded-[1.2rem] text-[10px] font-black uppercase tracking-wider border transition ${
                                    c.assigned_officer_id
                                      ? 'border-emerald-500/20 bg-emerald-500/10 text-emerald-400'
                                      : 'border-brand/20 bg-brand/10 text-brand-light hover:bg-brand/20'
                                  }`}
                                >
                                  {c.assigned_officer_id ? 'Assigned ✅' : 'Assign Squad'}
                                </button>
                              )}
                            </td>
                          </tr>
                        ))}
                        {filteredComplaints.length === 0 && (
                          <tr>
                            <td colSpan={5} className="py-8 text-center text-text-3 text-xs">{t('dashboard.no_complaints_matching', 'No complaints match filters')}</td>
                          </tr>
                        )}
                      </tbody>
                    </table>
                  </div>
                </SurfaceCard>
              </div>

              {/* Ward leaderboards */}
              <div className="flex flex-col gap-6">
                <SurfaceCard>
                  <div className="text-[10px] font-semibold uppercase tracking-[0.22em] text-text-3">{t('dashboard.ward_leaderboard', 'Ward Leaderboard')}</div>
                  <h3 className="mt-1 text-lg font-black font-space tracking-tight text-text-1 uppercase">{t('dashboard.resolution_rankings', 'RESOLUTION SPEED RANKINGS')}</h3>
                  
                  <div className="mt-5 divide-y divide-border/10">
                    {wards.map((w, index) => (
                      <div key={w.ward_id} className="py-3 flex items-center justify-between gap-3 text-xs">
                        <div className="flex items-center gap-3">
                          <span className="font-black text-text-3">{index + 1}</span>
                          <div>
                            <div className="font-bold text-text-1 dark:text-white uppercase tracking-wider">{w.ward_name}</div>
                            <div className="text-[10px] text-text-3 mt-0.5">{w.zone_name}</div>
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="font-black text-brand-light">{w.resolution_rate}%</div>
                          <div className="text-[9px] text-text-3 mt-0.5">{w.open_issues} Open / {w.sla_breach_count} Breached</div>
                        </div>
                      </div>
                    ))}
                  </div>
                </SurfaceCard>
              </div>
            </div>

          </div>
        )}

      </main>

      {/* ── Complaint Detail Side Panel ── */}
      {selectedComplaint && (
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 z-40 bg-black/40 backdrop-blur-sm lg:bg-transparent lg:backdrop-blur-none lg:pointer-events-none"
            onClick={() => setSelectedComplaint(null)}
          />
          {/* Panel */}
          <div className="fixed right-0 top-0 z-50 h-full w-full max-w-md bg-surface-1 border-l border-border shadow-2xl overflow-y-auto animate-in slide-in-from-right-5">
            <div className="p-6">
              {/* Close */}
              <button
                onClick={() => setSelectedComplaint(null)}
                className="mb-4 p-2 rounded-xl bg-surface-2 text-text-3 hover:text-text-1 hover:bg-surface-3 transition-colors"
              >
                <X size={20} />
              </button>

              {/* Ref */}
              <div className="text-[10px] font-semibold uppercase tracking-widest text-text-3">{t('dashboard.details.title', 'Complaint Details')}</div>
              <h2 className="mt-1 text-xl font-black text-text-1">
                {selectedComplaint.complaint_ref || selectedComplaint.uuid.slice(0, 8).toUpperCase()}
              </h2>

              {/* Status + Severity */}
              <div className="mt-4 flex items-center gap-2">
                <span className={`px-3 py-1 rounded-lg text-[10px] font-bold uppercase tracking-wider ${
                  selectedComplaint.status === 'resolved'
                    ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                    : selectedComplaint.status === 'in_progress'
                    ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                    : 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/20'
                }`}>
                  {selectedComplaint.status.replace('_', ' ')}
                </span>
                <span className={`px-3 py-1 rounded-lg text-[10px] font-bold uppercase tracking-wider ${
                  selectedComplaint.severity >= 4 ? 'bg-red-500/10 text-red-400 border border-red-500/20' : 'bg-brand/10 text-brand-light border border-brand/20'
                }`}>
                  {t('dashboard.details.severity_prefix', 'Severity')} {selectedComplaint.severity}
                </span>
              </div>

              {/* Category */}
              <div className="mt-6">
                <p className="text-[10px] font-semibold uppercase tracking-widest text-text-3 mb-1">{t('dashboard.details.category', 'Category')}</p>
                <p className="text-sm font-bold text-text-1">{selectedComplaint.category} — {selectedComplaint.issue_type}</p>
              </div>

              {/* Location */}
              <div className="mt-4">
                <p className="text-[10px] font-semibold uppercase tracking-widest text-text-3 mb-1">{t('dashboard.details.location', 'Location')}</p>
                <div className="flex items-start gap-2">
                  <MapPin size={14} className="text-brand-light mt-0.5 shrink-0" />
                  <p className="text-sm text-text-2">{selectedComplaint.location_address || 'Location pending'}</p>
                </div>
                {selectedComplaint.ward_name && (
                  <p className="text-xs text-text-3 mt-1 ml-5">{t('dashboard.details.ward_prefix', 'Ward: ')}{selectedComplaint.ward_name}</p>
                )}
              </div>

              {/* Description */}
              {selectedComplaint.description && (
                <div className="mt-4">
                  <p className="text-[10px] font-semibold uppercase tracking-widest text-text-3 mb-1">{t('dashboard.details.description', 'Description')}</p>
                  <p className="text-sm text-text-2 leading-relaxed">{selectedComplaint.description}</p>
                </div>
              )}

              {/* Timeline */}
              <div className="mt-6">
                <p className="text-[10px] font-semibold uppercase tracking-widest text-text-3 mb-3">{t('dashboard.details.timeline', 'Timeline')}</p>
                <div className="space-y-3">
                  <div className="flex items-center gap-3">
                    <div className="w-2 h-2 rounded-full bg-cyan-400" />
                    <div>
                      <p className="text-xs font-semibold text-text-1">{t('dashboard.details.created', 'Created')}</p>
                      <p className="text-[10px] text-text-3">{new Date(selectedComplaint.created_at).toLocaleString('en-IN')}</p>
                    </div>
                  </div>
                  {selectedComplaint.assigned_officer_id && (
                    <div className="flex items-center gap-3">
                      <div className="w-2 h-2 rounded-full bg-amber-400" />
                      <p className="text-xs font-semibold text-text-1">{t('dashboard.details.officer_assigned', 'Officer Assigned')}</p>
                    </div>
                  )}
                  {selectedComplaint.sla_deadline && (
                    <div className="flex items-center gap-3">
                      <div className={`w-2 h-2 rounded-full ${new Date(selectedComplaint.sla_deadline) < new Date() ? 'bg-red-400' : 'bg-brand-light'}`} />
                      <div>
                        <p className="text-xs font-semibold text-text-1">{t('dashboard.details.sla_deadline', 'SLA Deadline')}</p>
                        <p className="text-[10px] text-text-3">{new Date(selectedComplaint.sla_deadline).toLocaleString('en-IN')}</p>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}