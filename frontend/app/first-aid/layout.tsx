// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
import React from 'react';

import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'First Aid Guide',
  description: 'Emergency first aid procedures for road accidents, injuries, and medical emergencies — step-by-step guidance for bystanders and first responders.',
  keywords: ['first aid', 'emergency medical', 'CPR', 'road accident first aid', 'bystander care', 'injury response', 'medical emergency India'],
  openGraph: {
    title: 'SafeVixAI First Aid Guide',
    description: 'Step-by-step first aid procedures for road emergencies and injuries.',
    type: 'website',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'SafeVixAI First Aid Guide',
    description: 'Step-by-step first aid procedures for road emergencies and injuries.',
  },
};

export default function FirstAidLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
