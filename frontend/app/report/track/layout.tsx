// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
import React from 'react';

import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Track Report',
  description: 'Track the status of your submitted road issue reports. View updates, resolutions, and authority responses.',
  keywords: ['track report', 'report status', 'road issue tracking', 'complaint status', 'pothole report status'],
  openGraph: {
    title: 'SafeVixAI Report Tracker',
    description: 'Track the status of your submitted road issue reports.',
    type: 'website',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'SafeVixAI Report Tracker',
    description: 'Track the status of your submitted road issue reports.',
  },
};

export default function ReportTrackLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
