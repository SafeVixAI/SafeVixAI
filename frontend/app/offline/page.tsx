'use client';

// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
import React from 'react';


import Link from 'next/link';
import { AlertTriangle, BookOpen, MapPin, Phone, Siren } from 'lucide-react';
import { useTranslation } from 'react-i18next';

export default function OfflinePage() {
  const { t } = useTranslation('common');

  const EMERGENCY_NUMBERS = [
    { labelKey: 'common.police', defaultLabel: 'Police', number: '100' },
    { labelKey: 'common.ambulance', defaultLabel: 'Ambulance', number: '102' },
    { labelKey: 'common.fire', defaultLabel: 'Fire', number: '101' },
    { labelKey: 'common.women_helpline', defaultLabel: 'Women Helpline', number: '1091' },
    { labelKey: 'common.child_helpline', defaultLabel: 'Child Helpline', number: '1098' },
    { labelKey: 'common.national_emergency', defaultLabel: 'National Emergency', number: '112' },
    { labelKey: 'common.road_accident', defaultLabel: 'Road Accident (Highway)', number: '1033' },
  ];

  return (
    <main className="sv-page min-h-dvh px-5 py-10">
      <section className="mx-auto flex min-h-[calc(100dvh-5rem)] w-full max-w-lg flex-col justify-center gap-6">
        <div className="sv-card p-6">
          <div className="mb-5 flex h-12 w-12 items-center justify-center rounded-lg border border-emergency/30 bg-emergency/10 text-emergency">
            <AlertTriangle size={24} aria-hidden="true" />
          </div>
          <p className="sv-terminal-overline">{t('common.offline_mode', 'Offline Mode')}</p>
          <h1 className="mt-2 text-2xl font-black tracking-tight text-text-1">
            {t('common.offline_title', 'SafeVixAI is running from cached emergency tools.')}
          </h1>
          <p className="mt-3 text-sm font-medium leading-6 text-text-2">
            {t('common.offline_desc', 'Network services are unavailable right now. SOS, first aid, emergency numbers, and queued reports remain available.')}
          </p>
        </div>

        {/* Emergency phone numbers — always visible even offline */}
        <div className="sv-card p-4">
          <p className="mb-3 flex items-center gap-2 text-xs font-bold uppercase tracking-widest text-emergency">
            <Phone size={14} aria-hidden="true" />
            {t('common.emergency_numbers_title', 'Emergency Numbers')}
          </p>
          <div className="grid grid-cols-2 gap-2">
            {EMERGENCY_NUMBERS.map((item) => (
              <a
                key={item.number}
                href={`tel:${item.number}`}
                className="flex items-center justify-between rounded-lg border border-border-md bg-surface-2 px-3 py-2 text-sm transition hover:bg-surface-3"
              >
                <span className="text-text-2">{t(item.labelKey, item.defaultLabel)}</span>
                <span className="font-bold text-text-1">{item.number}</span>
              </a>
            ))}
          </div>
        </div>

        <div className="grid gap-3">
          <Link href="/sos" className="sv-card sv-card-interactive flex items-center gap-3 p-4">
            <Siren className="text-emergency" size={20} aria-hidden="true" />
            <span className="text-sm font-bold text-text-1">{t('common.open_sos', 'Open Emergency SOS')}</span>
          </Link>
          <Link href="/first-aid" className="sv-card sv-card-interactive flex items-center gap-3 p-4">
            <BookOpen className="text-brand" size={20} aria-hidden="true" />
            <span className="text-sm font-bold text-text-1">{t('common.open_first_aid', 'Open First Aid Guides')}</span>
          </Link>
          <Link href="/locator" className="sv-card sv-card-interactive flex items-center gap-3 p-4">
            <MapPin className="text-warning" size={20} aria-hidden="true" />
            <span className="text-sm font-bold text-text-1">{t('common.open_locator', 'Open Cached Locator')}</span>
          </Link>
        </div>
      </section>
    </main>
  );
}