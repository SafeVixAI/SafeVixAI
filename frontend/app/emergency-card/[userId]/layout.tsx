// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
import React from 'react';

import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Emergency Card',
  description: 'Emergency contact card — share your emergency contacts and medical information during a crisis.',
  robots: { index: false },
  openGraph: {
    title: 'SafeVixAI Emergency Card',
    description: 'Emergency contact and medical information card — shared via SafeVixAI.',
    type: 'website',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'SafeVixAI Emergency Card',
    description: 'Emergency contact and medical information card.',
  },
};

export default function EmergencyCardLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
