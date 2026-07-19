// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
import React from 'react';

import type { Metadata } from 'next';

interface PageProps {
  params: Promise<{ session_id: string }>;
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { session_id } = await params;
  const displayId = session_id.length > 8 ? session_id.slice(0, 8) + '...' : session_id;

  return {
    title: `Family Tracking - ${displayId}`,
    description: `Real-time family tracking session ${displayId}. Monitor live location of family members during travel for enhanced road safety.`,
    openGraph: {
      title: `Family Tracking ${displayId} | SafeVixAI`,
      description: 'Real-time family location tracking for road safety.',
      type: 'website',
    },
    twitter: {
      card: 'summary_large_image',
      title: `Family Tracking ${displayId} | SafeVixAI`,
      description: 'Real-time family location tracking for road safety.',
    },
    robots: { index: false, follow: false },
  };
}

export default function TrackSessionLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
