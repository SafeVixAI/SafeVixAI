// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
import React from 'react';

import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Bystander Mode',
  description: 'Assist accident victims with step-by-step guidance. Locate nearby hospitals, police, and emergency services as a bystander.',
  keywords: ['bystander', 'accident assistance', 'emergency help', 'first responder', 'road accident bystander'],
  openGraph: {
    title: 'SafeVixAI Bystander Mode',
    description: 'Step-by-step guidance to assist accident victims and locate emergency services.',
    type: 'website',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'SafeVixAI Bystander Mode',
    description: 'Step-by-step guidance to assist accident victims and locate emergency services.',
  },
};

export default function BystanderLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
