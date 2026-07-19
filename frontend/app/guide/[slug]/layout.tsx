// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
import React from 'react';

import type { Metadata } from 'next';

interface PageProps {
  params: Promise<{ slug: string }>;
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { slug } = await params;
  const title = slug
    .replace(/-/g, ' ')
    .replace(/\b\w/g, (c) => c.toUpperCase());

  return {
    title: `${title} - Municipality Guide`,
    description: `Comprehensive guide about ${title} — municipal services, road infrastructure projects, and civic information for your area.`,
    openGraph: {
      title: `${title} - Municipality Guide | SafeVixAI`,
      description: `Learn about ${title} — municipal services and road infrastructure.`,
      type: 'article',
    },
    twitter: {
      card: 'summary_large_image',
      title: `${title} - Municipality Guide | SafeVixAI`,
      description: `Learn about ${title} — municipal services and road infrastructure.`,
    },
  };
}

export default function GuideSlugLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
