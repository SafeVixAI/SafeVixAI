// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
import React from 'react';

import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Challan Calculator',
  description: 'Calculate traffic violation fines under the Motor Vehicles Act. Check challan amounts for speeding, drunk driving, no helmet, and more.',
  keywords: ['challan calculator', 'traffic fine', 'Motor Vehicles Act', 'traffic violation', 'speeding challan', 'drunk driving fine', 'India challan'],
  openGraph: {
    title: 'SafeVixAI Challan Calculator',
    description: 'Calculate traffic violation fines instantly under the Motor Vehicles Act.',
    type: 'website',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'SafeVixAI Challan Calculator',
    description: 'Calculate traffic violation fines instantly under the Motor Vehicles Act.',
  },
};

export default function ChallanLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
