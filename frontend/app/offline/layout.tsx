// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
import React from 'react';

import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Offline Mode',
  description: 'SafeVixAI offline resources — emergency numbers, first aid guides, and critical safety tools available without internet access.',
  keywords: ['offline mode', 'emergency offline', 'no internet safety', 'offline first aid', 'emergency contacts offline'],
  openGraph: {
    title: 'SafeVixAI Offline Mode',
    description: 'Critical safety tools and emergency information available without internet access.',
    type: 'website',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'SafeVixAI Offline Mode',
    description: 'Critical safety tools and emergency information available without internet access.',
  },
};

export default function OfflineLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
