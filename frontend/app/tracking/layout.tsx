// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
import React from 'react';

import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Live Tracking',
  description: 'Real-time family tracking dashboard — monitor live locations of family members, share trips, and ensure road safety with GPS tracking.',
  keywords: ['live tracking', 'family tracking', 'GPS tracking', 'real-time location', 'family safety', 'trip tracking'],
  openGraph: {
    title: 'SafeVixAI Live Tracking',
    description: 'Real-time family tracking dashboard for road safety and location monitoring.',
    type: 'website',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'SafeVixAI Live Tracking',
    description: 'Real-time family tracking dashboard for road safety and location monitoring.',
  },
};

export default function TrackingLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
