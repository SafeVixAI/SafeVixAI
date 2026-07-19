// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
import React from 'react';

import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Command Center',
  description: 'SafeVixAI command and control dashboard for monitoring road safety incidents, emergency responses, and live tracking in real-time.',
  keywords: ['command center', 'emergency dashboard', 'incident monitoring', 'road safety control', 'live tracking dashboard'],
  openGraph: {
    title: 'SafeVixAI Command Center',
    description: 'Real-time command and control dashboard for road safety monitoring.',
    type: 'website',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'SafeVixAI Command Center',
    description: 'Real-time command and control dashboard for road safety monitoring.',
  },
};

export default function CommandCenterLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
