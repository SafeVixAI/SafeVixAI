'use client';

// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team


import React from 'react';
import { Scale, ShieldAlert, ArrowLeft, HeartPulse, ShieldCheck, AlertCircle } from 'lucide-react';
import { useRouter } from 'next/navigation';
import SystemHeader from '@/components/dashboard/SystemHeader';
import { SurfaceCard } from '@/components/ui/SurfaceCard';

export default function TermsOfServicePage() {
  const router = useRouter();

  return (
    <div className="sv-page sv-aurora relative flex flex-col min-h-screen transition-colors duration-500 overflow-y-auto">
      {/* ── Navigation Header ── */}
      <SystemHeader title="Terms of Service Terminal" showBack={false} />

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
            <span className="text-[10px] font-semibold text-brand-light uppercase tracking-[0.1em] font-space leading-none">Citizen SLA Active</span>
          </div>
          <h1 className="text-4xl font-black tracking-tight text-text-1 uppercase font-space">
            Terms of Service
          </h1>
          <p className="text-sm font-medium text-text-3 font-space max-w-2xl leading-relaxed">
            Effective Date: May 28, 2026. Please read these terms carefully before accessing or using the SafeVixAI citizen integration system.
          </p>
        </section>

        {/* Main Content Card */}
        <SurfaceCard padding="lg" className="flex flex-col gap-8">
          
          {/* Section 1: Acceptable Use */}
          <div className="flex flex-col gap-2">
            <h2 className="text-lg font-bold text-text-1 uppercase font-space flex items-center gap-2">
              <ShieldCheck size={18} className="text-brand-light" />
              1. Scope & Acceptable Use
            </h2>
            <p className="text-xs font-medium text-text-2 leading-relaxed">
              SafeVixAI is a public safety platform built to provide offline emergency support, accident warning mechanisms, and deterministic traffic compliance calculators.
            </p>
            <ul className="list-disc pl-5 text-[11px] font-mono text-text-3 space-y-1 mt-2">
              <li><strong>Emergency Purposes:</strong> The SOS incident dispatch and family tracking triggers must only be used in real emergencies.</li>
              <li><strong>Accurate Reporting:</strong> Any road hazard report (e.g. pothole coordinates, traffic obstructions) must be submitted in good faith. False reporting, bot spam, or AI flooding will result in IP bans and potential regulatory action under traffic control codes.</li>
              <li><strong>Non-Commercial Use:</strong> The service is provided completely free of charge to all citizens and civic administrators.</li>
            </ul>
          </div>

          <div className="h-px bg-border" />

          {/* Section 2: SLA & Service Availability */}
          <div className="flex flex-col gap-2">
            <h2 className="text-lg font-bold text-text-1 uppercase font-space flex items-center gap-2">
              <ShieldAlert size={18} className="text-brand-light" />
              2. SLA & Emergency Disclaimer
            </h2>
            <p className="text-xs font-medium text-text-2 leading-relaxed">
              We strive to maintain a state-of-the-art infrastructure (featuring circuit breakers, automatic 9-provider fallback mechanisms, and robust local caching databases). However, citizens must agree to the following operational parameters:
            </p>
            <div className="mt-3 p-4 rounded-xl bg-surface-2 border border-border flex flex-col gap-2">
              <div className="flex items-center gap-2 text-[10px] font-bold text-emergency uppercase tracking-wider font-space">
                <AlertCircle size={14} className="text-emergency animate-pulse" />
                CRITICAL WARNING FOR EMERGENCIES:
              </div>
              <span className="text-[11px] font-medium text-text-3 leading-relaxed">
                SafeVixAI is a auxiliary support system and is NOT a substitute for direct government emergency channels. In critical situations where life or property is in immediate danger, you must ALWAYS dial <strong>112</strong> (Unified India Emergency), <strong>108</strong> (Medical Services), or <strong>101</strong> (Fire Department) directly using a telephone line, regardless of application status.
              </span>
            </div>
          </div>

          <div className="h-px bg-border" />

          {/* Section 3: Challan and Fine Disclaimer */}
          <div className="flex flex-col gap-2">
            <h2 className="text-lg font-bold text-text-1 uppercase font-space flex items-center gap-2">
              <Scale size={18} className="text-brand-light" />
              3. Challan Calculator Disclaimer
            </h2>
            <p className="text-xs font-medium text-text-2 leading-relaxed">
              SafeVixAI's Challan Calculator is a deterministic compliance estimation engine mapping values directly from the Motor Vehicles Act 2019 and state-level overrides.
            </p>
            <ul className="list-disc pl-5 text-[11px] font-mono text-text-3 space-y-1 mt-2">
              <li><strong>Estimation Only:</strong> All calculated liabilities are estimations. Final challan adjudications, fine values, and license suspension protocols are exclusively within the jurisdiction of the traffic police department.</li>
              <li><strong>Legal Counsel:</strong> Calculations do not constitute professional legal advice. Users are encouraged to refer to official department publications or consult with legal counsel to resolve actual traffic citation issues.</li>
            </ul>
          </div>

          <div className="h-px bg-border" />

          {/* Section 4: AI & Vector Processing limitations */}
          <div className="flex flex-col gap-2">
            <h2 className="text-lg font-bold text-text-1 uppercase font-space flex items-center gap-2">
              <HeartPulse size={18} className="text-brand-light" />
              4. Limit of Liability & Indemnity
            </h2>
            <p className="text-xs font-medium text-text-2 leading-relaxed font-space">
              SafeVixAI, its operators, creators, and developers shall not be liable for any direct, indirect, incidental, or consequential damages resulting from:
            </p>
            <ul className="list-disc pl-5 text-[11px] font-mono text-text-3 space-y-1 mt-2">
              <li>The use or inability to use the offline geocoding, routing, or tracking features.</li>
              <li>Calculations performed on the Challan Calculator terminal.</li>
              <li>Medical information retrieved from the bystander first-aid catalog.</li>
              <li>Network or satellite outages affecting real-time tracking accuracy.</li>
            </ul>
          </div>

          <div className="h-px bg-border" />

          {/* Contact Info */}
          <div className="p-5 rounded-2xl bg-surface-2 border border-border flex flex-col gap-2">
            <p className="text-[10px] font-bold text-text-1 uppercase tracking-widest flex items-center gap-1.5 font-space">
              <Scale size={12} className="text-brand-light" strokeWidth={2} />
              Governing Law
            </p>
            <p className="text-[11px] font-medium text-text-3 leading-relaxed">
              These terms are governed by and construed in accordance with the laws of the Republic of India. Any legal disputes are subject to the exclusive jurisdiction of the competent courts in Chennai, Tamil Nadu, India.
            </p>
          </div>

        </SurfaceCard>
      </main>
    </div>
  );
}