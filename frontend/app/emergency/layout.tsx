import React from 'react';

// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Emergency Locator',
  description: 'Find nearby hospitals, police stations, fire stations, and ambulances instantly. Emergency service locator with real-time directions.',
  keywords: ['emergency locator', 'nearby hospitals', 'police station', 'fire station', 'ambulance', 'emergency services', 'India emergency'],
  openGraph: {
    title: 'SafeVixAI Emergency Locator',
    description: 'Find nearby emergency services instantly — hospitals, police, fire stations, and ambulances.',
    type: 'website',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'SafeVixAI Emergency Locator',
    description: 'Find nearby emergency services instantly — hospitals, police, fire stations, and ambulances.',
  },
};

export default function EmergencyLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}

