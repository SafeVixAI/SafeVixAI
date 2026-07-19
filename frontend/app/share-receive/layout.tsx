// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
import React from 'react';

import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Share Receive',
  description: 'Receive shared locations and emergency information from other apps into SafeVixAI for quick navigation and response.',
  keywords: ['share receive', 'web share target', 'location share', 'emergency share', 'PWA share'],
  robots: { index: false, follow: false },
};

export default function ShareReceiveLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
