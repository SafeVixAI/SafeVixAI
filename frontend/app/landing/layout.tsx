// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
import React from 'react';

import type { Metadata } from 'next';
import './styles/landing.css';

export const metadata: Metadata = {
  title: 'SafeVixAI — AI-Powered Road Safety Intelligence Infrastructure',
  description:
    'India\'s next-generation AI road safety platform. Real-time accident detection, emergency response routing, hazard intelligence, and challan management — protecting 1.4 billion lives.',
  keywords: [
    'road safety', 'AI', 'emergency response', 'accident detection', 'India',
    'hazard reporting', 'challan', 'SOS', 'hospital routing', 'intelligence platform',
  ],
  openGraph: {
    title: 'SafeVixAI — AI Road Safety Intelligence',
    description: 'Real-time accident detection, emergency response, and hazard intelligence for India.',
    type: 'website',
    url: 'https://safevixai.github.io/SafeVixAI/',
    siteName: 'SafeVixAI',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'SafeVixAI — AI Road Safety Intelligence',
    description: 'India\'s AI-powered road safety infrastructure platform.',
  },
  robots: { index: true, follow: true },
};

export default function LandingLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="grain-overlay" data-theme="dark">
      {children}
    </div>
  );
}
