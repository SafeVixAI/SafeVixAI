// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
import React from 'react';

import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Privacy Policy',
  description: 'SafeVixAI privacy policy — how we protect your data, handle emergency information, and ensure your privacy on our road safety platform.',
  keywords: ['privacy policy', 'data protection', 'emergency privacy', 'SafeVixAI privacy', 'data security'],
  openGraph: {
    title: 'SafeVixAI Privacy Policy',
    description: 'How SafeVixAI protects your data and ensures your privacy.',
    type: 'website',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'SafeVixAI Privacy Policy',
    description: 'How SafeVixAI protects your data and ensures your privacy.',
  },
};

export default function PrivacyLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
