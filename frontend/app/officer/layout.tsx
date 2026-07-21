// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
import React from 'react';

import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Officer Portal',
  description: 'Traffic police officer portal for challan management, incident reporting, and road safety enforcement tools.',
  keywords: ['officer portal', 'traffic police', 'challan management', 'law enforcement', 'road safety officer'],
  openGraph: {
    title: 'SafeVixAI Officer Portal',
    description: 'Traffic police portal for challan management and road safety enforcement.',
    type: 'website',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'SafeVixAI Officer Portal',
    description: 'Traffic police portal for challan management and road safety enforcement.',
  },
  robots: { index: false, follow: false },
};

export default function OfficerLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
