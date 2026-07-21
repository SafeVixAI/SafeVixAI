// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
import React from 'react';

import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Emergency SOS',
  description: 'Activate emergency SOS — alert emergency contacts, share live location, and connect to nearby emergency services instantly.',
  keywords: ['SOS', 'emergency alert', 'panic button', 'emergency contacts', 'live location sharing', 'emergency SOS India'],
  openGraph: {
    title: 'SafeVixAI Emergency SOS',
    description: 'Instant emergency alert — notify contacts and share your location.',
    type: 'website',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'SafeVixAI Emergency SOS',
    description: 'Instant emergency alert — notify contacts and share your location.',
  },
};

export default function SosLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
