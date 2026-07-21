'use client';

// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team


import React from 'react';
import { ShieldCheck, Scale, ArrowLeft, Eye, HeartPulse, Trash2 } from 'lucide-react';
import { useRouter } from 'next/navigation';
import SystemHeader from '@/components/dashboard/SystemHeader';
import { SurfaceCard } from '@/components/ui/SurfaceCard';

export default function PrivacyPolicyPage() {
  const router = useRouter();

  return (
    <div className="sv-page sv-aurora relative flex flex-col min-h-screen transition-colors duration-500 overflow-y-auto">
      {/* ── Navigation Header ── */}
      <SystemHeader title="Privacy Policy Terminal" showBack={false} />

      <main className="flex-1 w-full max-w-4xl mx-auto pt-28 pb-44 px-5 sm:px-12 relative z-10 flex flex-col gap-8">
        {/* Back Button */}
        <button
          onClick={() => router.push('/settings')}
          className="flex items-center gap-2 text-xs font-semibold uppercase tracking-widest text-text-3 hover:text-text-1 transition-colors w-fit border border-border bg-surface-2/50 hover:bg-surface-3 px-4 py-2 rounded-xl"
        >
          <ArrowLeft size={14} />
          Back to Settings
        </button>

        {/* Hero Section */}
        <section className="flex flex-col gap-3">
          <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-brand-light/10 border border-brand-light/20 w-fit">
            <span className="w-1.5 h-1.5 rounded-full bg-brand-light animate-pulse"></span>
            <span className="text-[10px] font-semibold text-brand-light uppercase tracking-[0.1em] font-space leading-none">DPDP Act 2023 Compliant</span>
          </div>
          <h1 className="text-4xl font-black tracking-tight text-text-1 uppercase font-space">
            Privacy Policy
          </h1>
          <p className="text-sm font-medium text-text-3 font-space max-w-2xl leading-relaxed">
            Effective Date: May 28, 2026. This policy outlines how SafeVixAI collects, stores, protects, and deletes personal data in accordance with India's Digital Personal Data Protection (DPDP) Act 2023.
          </p>
        </section>

        {/* Main Content Card */}
        <SurfaceCard padding="lg" className="flex flex-col gap-8">
          
          {/* Section 1: Overview */}
          <div className="flex flex-col gap-2">
            <h2 className="text-lg font-bold text-text-1 uppercase font-space flex items-center gap-2">
              <Eye size={18} className="text-brand-light" />
              1. Information We Collect
            </h2>
            <p className="text-xs font-medium text-text-2 leading-relaxed">
              SafeVixAI is designed as an emergency-first, offline-resilient platform. We prioritize minimizing the collection of personally identifiable information (PII):
            </p>
            <ul className="list-disc pl-5 text-[11px] font-mono text-text-3 space-y-1 mt-2">
              <li><strong>Emergency Profile Data:</strong> Name, blood group, allergies, medical notes, and vehicle details are stored in your profile.</li>
              <li><strong>Emergency Contacts:</strong> Name, relationship, and contact numbers.</li>
              <li><strong>Location Data:</strong> Continuous satellite GPS coordinate sync (only activated during active group/family tracking or active SOS dispatch).</li>
              <li><strong>Incident Reports:</strong> Geospatial reports and hazard pictures submitted by you (or anonymous bystanders).</li>
            </ul>
          </div>

          <div className="h-px bg-border" />

          {/* Section 2: DPDP Compliance */}
          <div className="flex flex-col gap-2">
            <h2 className="text-lg font-bold text-text-1 uppercase font-space flex items-center gap-2">
              <ShieldCheck size={18} className="text-brand-light" />
              2. DPDP Act 2023 Compliance
            </h2>
            <p className="text-xs font-medium text-text-2 leading-relaxed">
              Under India's Digital Personal Data Protection (DPDP) Act 2023, SafeVixAI acts as a <strong>Data Fiduciary</strong>. We guarantee the following statutory rights for citizen data:
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-3">
              <div className="p-4 rounded-xl bg-surface-2 border border-border flex flex-col gap-1">
                <span className="text-[10px] font-bold text-brand-light uppercase tracking-wider font-space">Purpose Limitation</span>
                <span className="text-[11px] font-medium text-text-3">Your medical information and location tracks are used strictly for emergency dispatches and civic safety. They are never sold or shared.</span>
              </div>
              <div className="p-4 rounded-xl bg-surface-2 border border-border flex flex-col gap-1">
                <span className="text-[10px] font-bold text-brand-light uppercase tracking-wider font-space">Consent & Transparency</span>
                <span className="text-[11px] font-medium text-text-3">We collect location data only upon explicit, active consent during tracking or SOS activation. You can revoke consent in Settings at any time.</span>
              </div>
              <div className="p-4 rounded-xl bg-surface-2 border border-border flex flex-col gap-1">
                <span className="text-[10px] font-bold text-brand-light uppercase tracking-wider font-space">Data Erasure (Right to Forget)</span>
                <span className="text-[11px] font-medium text-text-3">Citizens possess the absolute right to delete all emergency profiles, tracking logs, and active reports securely via our systems.</span>
              </div>
              <div className="p-4 rounded-xl bg-surface-2 border border-border flex flex-col gap-1">
                <span className="text-[10px] font-bold text-brand-light uppercase tracking-wider font-space">Grievance Redressal</span>
                <span className="text-[11px] font-medium text-text-3">Any privacy-related queries, reports of data breach, or grievance requests are resolved within 72 hours by our Data Protection Officer.</span>
              </div>
            </div>
          </div>

          <div className="h-px bg-border" />

          {/* Section 3: Data Deletion */}
          <div className="flex flex-col gap-2">
            <h2 className="text-lg font-bold text-text-1 uppercase font-space flex items-center gap-2">
              <Trash2 size={18} className="text-red-500" />
              3. Right to Erasure & Deletion
            </h2>
            <p className="text-xs font-medium text-text-2 leading-relaxed">
              We respect your right to have your data erased. You can immediately purge all emergency profiles and associated reports.
            </p>
            <div className="mt-3 p-4 rounded-2xl bg-red-500/5 border border-red-500/10 flex flex-col gap-2">
              <p className="text-[11px] font-bold text-red-500 uppercase tracking-widest font-mono">How to trigger absolute data erasure:</p>
              <p className="text-[11px] font-medium text-text-2 leading-relaxed">
                Go to the <strong>Settings Terminal</strong> and scroll down to <strong>Data Storage & Purge</strong>. Clicking the "Purge System Data" button will trigger a secure HTTP <code>DELETE</code> call to our databases, securely deleting your profile, active SOS incidents, and reported road hazards.
              </p>
            </div>
          </div>

          <div className="h-px bg-border" />

          {/* Section 4: AI & Vector Processing */}
          <div className="flex flex-col gap-2">
            <h2 className="text-lg font-bold text-text-1 uppercase font-space flex items-center gap-2">
              <Scale size={18} className="text-brand-light" />
              4. AI Vector & LLM Privacy
            </h2>
            <p className="text-xs font-medium text-text-2 leading-relaxed font-space">
              Our AI chat assistant operates via safe neural embeddings. 
            </p>
            <ul className="list-disc pl-5 text-[11px] font-mono text-text-3 space-y-1 mt-2">
              <li><strong>Local Vector Processing:</strong> Your search terms are hashed or vectorized locally on-device where possible.</li>
              <li><strong>LLM Provider Safeguards:</strong> Queries sent to our 9-provider fallback chain (including Groq, Google, Mistral) are strictly governed by enterprise Data Processing Agreements (DPAs), ensuring queries are never used for training third-party foundation models.</li>
            </ul>
          </div>

          <div className="h-px bg-border" />

          {/* DPO Contact Info */}
          <div className="p-5 rounded-2xl bg-surface-2 border border-border flex flex-col gap-2">
            <p className="text-[10px] font-bold text-text-1 uppercase tracking-widest flex items-center gap-1.5 font-space">
              <HeartPulse size={12} className="text-brand-light" />
              Data Protection Officer (DPO) Contact
            </p>
            <p className="text-[11px] font-medium text-text-3 leading-relaxed">
              If you have any questions regarding this Privacy Policy or DPDP statutory rights, contact our privacy desk at <code>dpo@safevixai.gov.in</code>.
            </p>
          </div>

        </SurfaceCard>
      </main>
    </div>
  );
}