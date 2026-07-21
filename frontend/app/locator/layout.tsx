// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
import React from 'react';

import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Service Locator',
  description: 'Locate emergency services, hospitals, police stations, and essential facilities near you with interactive maps.',
  keywords: ['service locator', 'nearby services', 'hospital locator', 'police locator', 'emergency map', 'India'],
  openGraph: {
    title: 'SafeVixAI Service Locator',
    description: 'Find essential services near you — hospitals, police stations, and emergency facilities.',
    type: 'website',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'SafeVixAI Service Locator',
    description: 'Find essential services near you — hospitals, police stations, and emergency facilities.',
  },
};

export default function LocatorLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
