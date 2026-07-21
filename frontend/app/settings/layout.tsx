// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
import React from 'react';

import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Settings',
  description: 'Customize your SafeVixAI experience — theme preferences, notification settings, language, offline data management, and more.',
  keywords: ['settings', 'preferences', 'theme', 'notifications', 'language', 'offline data', 'app settings'],
  robots: { index: false, follow: false },
};

export default function SettingsLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
