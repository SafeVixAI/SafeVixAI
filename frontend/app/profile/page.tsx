'use client';

// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team


import React, { useState, useEffect } from 'react';


import Image from 'next/image';
import {
  User, Shield, ShieldCheck, CheckCircle,
  Car, LogOut,
  CloudOff, ShieldAlert, Award,
  Heart, Star, Edit3, Save, X, Bell
} from 'lucide-react';
import { useAppStore, type UserProfile } from '@/lib/store';
import TopSearch from '@/components/dashboard/TopSearch';
import { TerminalHeader } from '@/components/ui/TerminalHeader';
import { SurfaceCard } from '@/components/ui/SurfaceCard';
import { SettingRow } from '@/components/ui/SettingRow';
import Toggle from '@/components/dashboard/Toggle';
import QREmergencyCard from '@/components/profile/QREmergencyCard';
import { usePageEntry } from '@/hooks/usePageEntry';
import { useShallow } from 'zustand/react/shallow';
import { track } from '@/lib/analytics';
import { toast } from 'sonner';
import { getOrCreateGuestId, getGuestProfile, updateGuestProfile, isGuestMode } from '@/lib/guest-auth';

export default function ProfilePage() {
  const { crashDetectionEnabled, setCrashDetectionEnabled, userProfile, setUserProfile, clearAuth, isAuthenticated } = useAppStore(useShallow((s) => ({ crashDetectionEnabled: s.crashDetectionEnabled, setCrashDetectionEnabled: s.setCrashDetectionEnabled, userProfile: s.userProfile, setUserProfile: s.setUserProfile, clearAuth: s.clearAuth, isAuthenticated: s.isAuthenticated })));
  const pageRef = usePageEntry();

  const [offlineMode, setOfflineMode] = useState(false);
  const [pushNotifs, setPushNotifs] = useState(true);
  const [showPurgeConfirm, setShowPurgeConfirm] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [editDraft, setEditDraft] = useState({ ...userProfile });
  const [saveFlash, setSaveFlash] = useState(false);

  useEffect(() => { document.title = 'Profile | SafeVixAI'; }, []);

  // Sync draft when not editing (e.g. external store update)
  useEffect(() => {
    if (!isEditing) setEditDraft({ ...userProfile });
  }, [isEditing, userProfile]);

  const handleEdit = () => {
    setEditDraft({ ...userProfile });
    setIsEditing(true);
  };

  const handleSave = () => {
    setUserProfile(editDraft);
    setIsEditing(false);
    setSaveFlash(true);
    track.profileCompleted();
    // Sync to guest profile if in guest mode
    if (!isAuthenticated) {
      const guestProfile = getGuestProfile();
      const firstContact = editDraft.emergencyContacts?.[0];
      updateGuestProfile({
        bloodGroup: editDraft.bloodGroup || guestProfile?.bloodGroup,
        preferredLanguage: editDraft.preferredLanguage || guestProfile?.preferredLanguage,
        emergencyContacts: editDraft.emergencyContacts.length > 0
          ? editDraft.emergencyContacts
          : (firstContact ? [{ name: firstContact.name || '', phone: firstContact.phone || '', relation: firstContact.relation || '' }] : guestProfile?.emergencyContacts),
      });
    }
    setTimeout(() => setSaveFlash(false), 2000);
  };

  const handleCancel = () => {
    setEditDraft({ ...userProfile });
    setIsEditing(false);
  };

  const handlePurge = () => {
    if (!showPurgeConfirm) {
      setShowPurgeConfirm(true);
      setTimeout(() => setShowPurgeConfirm(false), 3000);
    } else {
      window.localStorage.removeItem('safevixai:assistant-session');
      toast.success('Local session data purged.');
      setShowPurgeConfirm(false);
    }
  };

  // Initialize guest session on mount if not authenticated
  useEffect(() => {
    if (!isAuthenticated) {
      const guestId = getOrCreateGuestId();
      const guestProfile = getGuestProfile();
      if (!userProfile.id) {
        setUserProfile({ id: guestId });
      }
      if (guestProfile) {
        const updates: Partial<UserProfile> = {};
        if (guestProfile.bloodGroup) updates.bloodGroup = guestProfile.bloodGroup as UserProfile['bloodGroup'];
        if (guestProfile.emergencyContacts && guestProfile.emergencyContacts.length > 0) {
          updates.emergencyContacts = guestProfile.emergencyContacts;
          updates.emergencyContact = guestProfile.emergencyContacts[0]?.phone ?? '';
        }
        if (guestProfile.preferredLanguage) updates.preferredLanguage = guestProfile.preferredLanguage;
        if (Object.keys(updates).length > 0) setUserProfile(updates);
      }
    }
  }, [isAuthenticated, userProfile.id, setUserProfile]);

  // Derive a display ID from the user profile
  const displayId = userProfile.id || 'NOT SET';

  return (
    <div ref={pageRef} className="sv-page relative flex flex-col overflow-x-hidden transition-colors duration-500">
      <h1 className="sr-only">User Profile</h1>

      {/* ── Unified Tactical Navigation Header ── */}
      <TerminalHeader title="Operator Identity Matrix" subtitle="PROFILE & SETTINGS" />

      <div className="lg:hidden relative z-[100]">
        <TopSearch isMapPage={false} forceShow={true} showBack={false} />
      </div>
      <main className="flex-1 w-full max-w-2xl mx-auto pt-28 lg:pt-24 pb-44 px-6 space-y-12 relative z-10">

        {/* ── Save Flash Banner ── */}
        {saveFlash && (
          <div
            className="fixed top-24 left-1/2 -translate-x-1/2 z-50 flex items-center gap-2 bg-brand-light text-white px-6 py-3 rounded-full shadow-xl text-sm font-semibold uppercase tracking-widest"
          >
            <CheckCircle size={16} />
            Profile Saved
          </div>
        )}

        {/* ── Section 1: Hero Identity Matrix ── */}
        <section className="flex flex-col gap-8 relative">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-brand-light/10 border border-brand-light/20 w-fit">
              <span className="w-1.5 h-1.5 rounded-full bg-brand-light animate-pulse"></span>
              <span className="text-[10px] font-semibold text-brand-dim dark:text-brand-light uppercase tracking-[0.1em] font-space leading-none">Profile Matrix Sync</span>
            </div>

            {/* Edit / Save / Cancel controls */}
            {!isEditing ? (
              <button
                onClick={handleEdit}
                className="flex items-center gap-2 px-4 py-2 rounded-full bg-surface-2 dark:bg-white/10 border border-border dark:border-white/10 text-text-2 dark:text-text-3 text-[10px] font-semibold uppercase tracking-widest hover:bg-brand-light/10 hover:text-brand dark:hover:bg-brand/10 dark:hover:text-brand-light transition-all"
              >
                <Edit3 size={12} />
                Edit Profile
              </button>
            ) : (
              <div className="flex items-center gap-2">
                <button
                  onClick={handleCancel}
                  className="flex items-center gap-1 px-3 py-2 rounded-full bg-surface-2 dark:bg-white/10 border border-border dark:border-white/10 text-text-3 text-[10px] font-semibold uppercase tracking-widest hover:text-red-500 transition-all"
                >
                  <X size={12} />
                  Cancel
                </button>
                <button
                  onClick={handleSave}
                  className="flex items-center gap-1 px-4 py-2 rounded-full bg-brand-light text-white text-[10px] font-semibold uppercase tracking-widest hover:bg-brand transition-all shadow-lg"
                >
                  <Save size={12} />
                  Save
                </button>
              </div>
            )}
          </div>

          <div className="flex flex-col sm:flex-row items-center gap-8 relative z-10">
            <div className="relative group">
              {isEditing ? (
                <div className="flex flex-col items-center gap-2">
                  <div className="w-32 h-32 rounded-full border-4 border-white dark:border-white/10 overflow-hidden relative shadow-2xl bg-[var(--brand-dim)] flex items-center justify-center text-[var(--brand-light)] text-4xl font-black uppercase">
                    {editDraft.photo ? (
                      <Image src={editDraft.photo} alt={editDraft.name || ''} fill className="object-cover" />
                    ) : (
                      <span>{editDraft.name ? editDraft.name.split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase() : '?'}</span>
                    )}
                  </div>
                  <input
                    type="text"
                    value={editDraft.photo || ''}
                    onChange={e => setEditDraft(d => ({ ...d, photo: e.target.value }))}
                    placeholder="Avatar Image URL"
                    aria-label="Avatar Image URL"
                    className="text-[10px] w-28 bg-surface-2 dark:bg-white/5 border border-border p-1 rounded text-center outline-none text-text-2"
                  />
                </div>
              ) : (
                <>
                  <div className="w-32 h-32 rounded-full border-4 border-white dark:border-white/10 overflow-hidden relative shadow-2xl transition-transform duration-500 group-hover:scale-105 bg-[var(--brand-dim)] flex items-center justify-center text-[var(--brand-light)] text-4xl font-black uppercase">
                    {userProfile.photo ? (
                      <Image src={userProfile.photo} alt={userProfile.name} fill className="object-cover" />
                    ) : userProfile.name ? (
                      <span>{userProfile.name.split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase()}</span>
                    ) : (
                      <User size={40} className="text-text-4 dark:text-white/20" />
                    )}
                  </div>
                  <div className="absolute -bottom-2 -right-2 bg-brand-light w-10 h-10 rounded-lg flex items-center justify-center border-4 border-white dark:border-bg shadow-lg">
                    <CheckCircle size={20} className="text-white" />
                  </div>
                </>
              )}
            </div>

            <div className="text-center sm:text-left flex flex-col gap-2 flex-1">
              {isEditing ? (
                <div className="flex flex-col gap-2 w-full">
                  <input
                    type="text"
                    value={editDraft.name}
                    onChange={e => setEditDraft(d => ({ ...d, name: e.target.value }))}
                    placeholder="Your Full Name"
                    aria-label="Full Name"
                    className="text-3xl font-black tracking-tight text-text-1 dark:text-white uppercase font-space leading-none bg-transparent border-b-2 border-brand-light outline-none placeholder:text-text-4 dark:placeholder:text-white/20 w-full"
                  />
                  <input
                    type="text"
                    value={editDraft.subtitle || ''}
                    onChange={e => setEditDraft(d => ({ ...d, subtitle: e.target.value }))}
                    placeholder="Operator Subtitle (e.g. TACTICAL RESPONDER)"
                    aria-label="Operator Subtitle"
                    className="text-xs font-semibold tracking-tight text-text-2 dark:text-text-3 uppercase font-space bg-transparent border-b border-brand-light/40 outline-none placeholder:text-text-4 dark:placeholder:text-white/20 w-full"
                  />
                </div>
              ) : (
                <div className="flex flex-col gap-1.5">
                  <h2 className="text-4xl font-black tracking-tight text-text-1 dark:text-white uppercase font-space leading-none">
                    {userProfile.name || <span className="text-text-4 dark:text-white/20">Set Your Name</span>}
                  </h2>
                  {userProfile.subtitle && (
                    <p className="text-xs font-semibold text-text-2 dark:text-text-3 uppercase tracking-wider">
                      {userProfile.subtitle}
                    </p>
                  )}
                </div>
              )}
              <div className="flex items-center justify-center sm:justify-start gap-2 mt-1">
                <div className="px-2 py-1 bg-surface-2 dark:bg-white/5 rounded-lg border border-border dark:border-white/10">
                  <span className="text-[9px] font-semibold text-text-3 dark:text-brand-light uppercase tracking-widest leading-none">ID: {displayId}</span>
                </div>
                <div className="px-2 py-1 bg-warning/10 rounded-lg border border-warning/20 flex items-center gap-1">
                  <Award size={10} className="text-warning-dim dark:text-warning" />
                  <span className="text-[9px] font-semibold text-warning-dim dark:text-warning uppercase tracking-widest leading-none">SafeVixAI</span>
                </div>
              </div>
            </div>
          </div>

          {/* Vitals HUD Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <SurfaceCard padding="md" className="flex flex-col gap-4">
              <div className="flex items-center justify-between">
                <p className="text-[10px] font-semibold text-text-2 uppercase tracking-widest">Active Vessel</p>
                <Car size={16} className="text-brand-light" />
              </div>
              <div className="flex flex-col">
                {isEditing ? (
                  <input
                    type="text"
                    value={editDraft.vehicleNumber}
                    onChange={e => setEditDraft(d => ({ ...d, vehicleNumber: e.target.value }))}
                    placeholder="MH 01 AB 1234"
                    aria-label="Vehicle Number"
                    className="text-xl font-black text-text-1 dark:text-white uppercase tracking-tighter bg-transparent border-b-2 border-brand-light/60 outline-none placeholder:text-text-4 dark:placeholder:text-white/20"
                  />
                ) : (
                  <span className="text-xl font-black text-text-1 dark:text-white uppercase tracking-tighter">
                    {userProfile.vehicleNumber || <span className="text-text-4 dark:text-white/20">Not Set</span>}
                  </span>
                )}
                <span className="text-[10px] font-bold text-text-2 uppercase mt-1">VEHICLE_REGISTRATION</span>
              </div>
            </SurfaceCard>

            <SurfaceCard padding="md" className="flex flex-col gap-4">
              <div className="flex items-center justify-between">
                <p className="text-[10px] font-semibold text-text-2 uppercase tracking-widest">Bio Signature</p>
                <Heart size={16} className="text-red-500" />
              </div>
              <div className="flex flex-col">
                {isEditing ? (
                  <select
                    value={editDraft.bloodGroup}
                    onChange={e => setEditDraft(d => ({ ...d, bloodGroup: e.target.value as UserProfile['bloodGroup'] }))}
                    aria-label="Blood Group"
                    className="text-xl font-black text-text-1 dark:text-white uppercase tracking-tighter bg-surface-2 dark:bg-white/5 border border-border rounded p-1 outline-none"
                  >
                    <option value="">Select Blood Group</option>
                    {['A+', 'A-', 'B+', 'B-', 'O+', 'O-', 'AB+', 'AB-', 'Unknown'].map((g) => (
                      <option key={g} value={g}>{g}</option>
                    ))}
                  </select>
                ) : (
                  <span className="text-xl font-black text-text-1 dark:text-white uppercase tracking-tighter">
                    {userProfile.bloodGroup || <span className="text-text-4 dark:text-white/20">Not Set</span>}
                  </span>
                )}
                <span className="text-[10px] font-bold text-text-2 uppercase mt-1">EMERGENCY_BROADCAST_ON</span>
              </div>
            </SurfaceCard>

            {/* Operator Mobile Links */}
            <SurfaceCard padding="md" className="flex flex-col gap-4">
              <div className="flex items-center justify-between">
                <p className="text-[10px] font-semibold text-text-2 uppercase tracking-widest">Phone Signature</p>
                <User size={16} className="text-brand dark:text-brand-light" />
              </div>
              <div className="flex flex-col">
                {isEditing ? (
                  <input
                    type="text"
                    value={editDraft.phone || ''}
                    onChange={e => setEditDraft(d => ({ ...d, phone: e.target.value }))}
                    placeholder="+91 98765 43210"
                    aria-label="Phone Number"
                    className="text-xl font-black text-text-1 dark:text-white tracking-tighter bg-transparent border-b-2 border-brand/60 outline-none placeholder:text-text-4 dark:placeholder:text-white/20"
                  />
                ) : (
                  <span className="text-xl font-black text-text-1 dark:text-white tracking-tighter">
                    {userProfile.phone || <span className="text-text-4 dark:text-white/20">Not Set</span>}
                  </span>
                )}
                <span className="text-[10px] font-bold text-text-2 uppercase mt-1">OPERATOR_MOBILE_LINK</span>
              </div>
            </SurfaceCard>

            {/* Biometric Anomalies */}
            <SurfaceCard padding="md" className="flex flex-col gap-4">
              <div className="flex items-center justify-between">
                <p className="text-[10px] font-semibold text-text-2 uppercase tracking-widest">Medical Record</p>
                <ShieldCheck size={16} className="text-brand dark:text-brand-light" />
              </div>
              <div className="flex flex-col">
                {isEditing ? (
                  <input
                    type="text"
                    value={editDraft.medicalConditions || ''}
                    onChange={e => setEditDraft(d => ({ ...d, medicalConditions: e.target.value }))}
                    placeholder="e.g. Asthma, Penicillin allergy"
                    aria-label="Medical Conditions"
                    className="text-xl font-black text-text-1 dark:text-white tracking-tighter bg-transparent border-b-2 border-brand/60 outline-none placeholder:text-text-4 dark:placeholder:text-white/20"
                  />
                ) : (
                  <span className="text-xl font-black text-text-1 dark:text-white tracking-tighter truncate max-w-xs">
                    {userProfile.medicalConditions || <span className="text-text-4 dark:text-white/20">None</span>}
                  </span>
                )}
                <span className="text-[10px] font-bold text-text-2 uppercase mt-1">BIOMETRIC_ANOMALIES</span>
              </div>
            </SurfaceCard>

            {/* Emergency Contact — full width */}
            <SurfaceCard padding="md" className="sm:col-span-2 flex flex-col gap-4">
              <div className="flex items-center justify-between">
                <p className="text-[10px] font-semibold text-text-2 uppercase tracking-widest">Emergency Contact</p>
                <Shield size={16} className="text-brand dark:text-brand-light" />
              </div>
              <div className="flex flex-col">
                {isEditing ? (
                  <input
                    type="tel"
                    value={editDraft.emergencyContact}
                    onChange={e => setEditDraft(d => ({ ...d, emergencyContact: e.target.value }))}
                    placeholder="+91 98765 43210"
                    aria-label="Emergency Contact"
                    className="text-xl font-black text-text-1 dark:text-white tracking-tighter bg-transparent border-b-2 border-brand/60 outline-none placeholder:text-text-4 dark:placeholder:text-white/20"
                  />
                ) : (
                  <span className="text-xl font-black text-text-1 dark:text-white tracking-tighter">
                    {userProfile.emergencyContact || <span className="text-text-4 dark:text-white/20 font-normal text-base">Add emergency contact</span>}
                  </span>
                )}
                <span className="text-[10px] font-bold text-text-2 uppercase mt-1">SOS_DISPATCH_CONTACT</span>
              </div>
            </SurfaceCard>
          </div>
        </section>

        {/* ── Section: QR Emergency Card ── */}
        <QREmergencyCard />

        {/* ── Section 2: Operational Protocols ── */}
        <section className="flex flex-col gap-6">
          <h3 className="text-[10px] font-semibold uppercase tracking-[0.1em] text-text-2 font-space px-2">Mission Protocol</h3>
          <SurfaceCard padding="md">
            {[
              { id: 'offline', icon: <CloudOff size={18} />, label: 'V8 Offline Mode', sub: 'Process locally, no network leakage', state: offlineMode, toggle: setOfflineMode },
              { id: 'crash', icon: <ShieldAlert size={18} />, label: 'Crash Detection', sub: 'Instant satellite SOS engagement', state: crashDetectionEnabled, toggle: setCrashDetectionEnabled },
              { id: 'notify', icon: <Bell size={18} />, label: 'Push Hub', sub: 'Critical hazard & P0 alerts', state: pushNotifs, toggle: setPushNotifs },
            ].map(item => (
              <SettingRow
                key={item.id}
                icon={<div className={item.state ? 'text-brand-light' : 'text-text-2'}>{item.icon}</div>}
                title={item.label}
                description={item.sub}
                rightElement={<Toggle checked={item.state} onChange={item.toggle} ariaLabel={`Toggle ${item.label}`} />}
              />
            ))}
          </SurfaceCard>
        </section>

        {/* ── Section 3: Achievements & Legacy ── */}
        <section className="flex flex-col gap-6">
          <h3 className="text-[10px] font-semibold uppercase tracking-[0.1em] text-text-2 font-space px-2">Tactical Awards</h3>
          <div className="flex gap-4 overflow-x-auto pb-6 -mx-6 px-6 scrollbar-thin scrollbar-thumb-border-md dark:scrollbar-thumb-surface-3 scrollbar-track-transparent">
            {[
              { title: 'Road Safety', score: 'Active User', bgColor: 'bg-brand-light/10', iconColor: 'text-brand-light' },
              { title: 'First Responder', score: 'Trained', bgColor: 'bg-warning/10', iconColor: 'text-warning' },
              { title: 'AI Master', score: 'SafeVixAI', bgColor: 'bg-brand/10', iconColor: 'text-brand dark:text-brand-light' },
            ].map(badge => (
              <SurfaceCard key={badge.title} padding="md" className="flex-shrink-0 w-40 flex flex-col items-center gap-3">
                <div className={`p-4 rounded-xl ${badge.bgColor}`}>
                  <Star size={24} className={badge.iconColor} />
                </div>
                <div className="text-center">
                  <p className="text-[10px] font-semibold text-text-1 dark:text-white uppercase tracking-tight leading-none">{badge.title}</p>
                  <p className="text-[9px] font-bold text-text-2 uppercase tracking-widest mt-2">{badge.score}</p>
                </div>
              </SurfaceCard>
            ))}
          </div>
        </section>

        {/* Action Panel */}
        <section className="flex flex-col items-center gap-4 pt-10">
          {/* Sign Out — only if using real auth */}
          {isAuthenticated && (
            <button
              onClick={() => { clearAuth(); }}
              className="w-full h-14 rounded-full border-2 border-brand/30 bg-brand/10 hover:bg-brand/20 text-[10px] font-semibold uppercase tracking-[0.1em] text-brand dark:text-brand-light flex items-center justify-center gap-2 transition-all active:scale-95"
            >
              <LogOut size={14} />
              Sign Out Operator
            </button>
          )}
          {!isAuthenticated && isGuestMode() && (
            <div className="flex items-center gap-2 px-4 py-2 rounded-full bg-surface-2 dark:bg-white/5 border border-border text-text-3 text-[10px] font-semibold uppercase tracking-widest">
              <Shield size={12} />
              Guest Mode — Data stored locally
            </div>
          )}
          <button
            onClick={handlePurge}
            className={`h-14 px-10 rounded-full border-2 text-[10px] font-semibold uppercase tracking-[0.1em] transition-all active:scale-95 ${showPurgeConfirm
                ? 'border-red-500 bg-red-500/10 text-red-500'
                : 'border-border dark:border-white/10 text-text-2 hover:text-red-500 hover:border-red-500/20'
              }`}
          >
            {showPurgeConfirm ? 'CONFIRM PURGE?' : 'PURGE LOCAL SESSION'}
          </button>
          <p className="text-[9px] font-semibold text-text-3 dark:text-text-3 uppercase tracking-[0.1em]">Sentinel V4.2 Real-time Security Layer</p>
        </section>

      </main>
    </div>
  );
}