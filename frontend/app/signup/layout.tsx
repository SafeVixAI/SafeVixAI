// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
import React from 'react';

import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Sign Up',
  description: 'Create a SafeVixAI account to access emergency profiles, family tracking, and personalized road safety tools.',
  keywords: ['sign up', 'register', 'create account', 'SafeVixAI registration', 'emergency account'],
  robots: { index: false, follow: false },
};

export default function SignupLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
