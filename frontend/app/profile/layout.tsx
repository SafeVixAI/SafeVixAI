// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
import React from 'react';

import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Profile',
  description: 'Manage your SafeVixAI profile, emergency contacts, blood group, and personal safety preferences.',
  keywords: ['user profile', 'emergency contacts', 'blood group', 'safety profile', 'personal information'],
  robots: { index: false, follow: false },
};

export default function ProfileLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
