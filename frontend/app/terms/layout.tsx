// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
import React from 'react';

import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Terms of Service',
  description: 'SafeVixAI terms of service — terms and conditions for using our AI-powered road safety platform and emergency services.',
  keywords: ['terms of service', 'terms and conditions', 'SafeVixAI terms', 'legal', 'road safety platform'],
  openGraph: {
    title: 'SafeVixAI Terms of Service',
    description: 'Terms and conditions for using the SafeVixAI road safety platform.',
    type: 'website',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'SafeVixAI Terms of Service',
    description: 'Terms and conditions for using the SafeVixAI road safety platform.',
  },
};

export default function TermsLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
