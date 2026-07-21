// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
import React from 'react';

import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Municipality Guides',
  description: 'Browse municipal corporation guides for road safety, infrastructure projects, contractor information, and civic services.',
  keywords: ['municipality guide', 'civic services', 'road infrastructure', 'contractor information', 'municipal corporation'],
  openGraph: {
    title: 'SafeVixAI Municipality Guides',
    description: 'Municipal corporation guides for road safety, infrastructure, and civic services.',
    type: 'website',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'SafeVixAI Municipality Guides',
    description: 'Municipal corporation guides for road safety, infrastructure, and civic services.',
  },
};

export default function GuideLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
