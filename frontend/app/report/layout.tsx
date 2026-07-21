// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
import React from 'react';

import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Report Road Issue',
  description: 'Report road hazards, potholes, accidents, and infrastructure issues to authorities. Upload photos and track report status.',
  keywords: ['road report', 'pothole report', 'road hazard', 'accident report', 'infrastructure issue', 'road damage', 'India roads'],
  openGraph: {
    title: 'SafeVixAI Road Issue Reporter',
    description: 'Report road hazards, potholes, and infrastructure issues. Track your report status.',
    type: 'website',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'SafeVixAI Road Issue Reporter',
    description: 'Report road hazards, potholes, and infrastructure issues. Track your report status.',
  },
};

export default function ReportLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
