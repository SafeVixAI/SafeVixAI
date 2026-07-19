// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
import React from 'react';

import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'AI Assistant',
  description: 'Chat with SafeVixAI about traffic laws, first aid, road safety, and more. Get instant answers from our AI-powered roadside assistant.',
  keywords: ['AI assistant', 'chatbot', 'traffic laws', 'first aid', 'road safety', 'India traffic rules'],
  openGraph: {
    title: 'SafeVixAI Assistant',
    description: 'Get instant answers about road safety from our AI chatbot.',
    type: 'website',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'SafeVixAI Assistant',
    description: 'Get instant answers about road safety from our AI chatbot.',
  },
};

export default function AssistantLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
