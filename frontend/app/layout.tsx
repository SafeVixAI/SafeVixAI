// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
import React from 'react';

import type { Metadata, Viewport } from 'next';
import Script from 'next/script';
import { Toaster } from 'sonner';
import { headers } from 'next/headers';
import { SWRConfig } from 'swr';
import { Inter, Space_Grotesk, JetBrains_Mono } from 'next/font/google';
import './globals.css';
import { ConnectivityProvider } from '@/components/ConnectivityProvider';
import { ThemeProvider } from '@/components/ThemeProvider';
import { PUBLIC_API_BASE_URL, PUBLIC_CHATBOT_BASE_URL } from '@/lib/public-env';
import { GSAPProvider } from '@/components/providers/GSAPProvider';
import { SentryInit } from '@/components/providers/SentryInit';
import { ViewTransitions } from 'next-view-transitions';
import { AppFrame } from '@/components/ui/AppFrame';
import { AnalyticsProvider } from '@/lib/analytics-provider';
import { EnterpriseClientAppHooks } from '@/components/EnterpriseClientAppHooks';
import PwaUpdatePrompt from '@/components/updates/PwaUpdatePrompt';

const inter = Inter({
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-inter',
  weight: ['300', '400', '500', '600', '700', '800'],
});

const spaceGrotesk = Space_Grotesk({
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-space',
  weight: ['400', '500', '600', '700'],
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-mono',
  weight: ['400', '500', '600', '700'],
});

const BASE_URL = process.env.NEXT_PUBLIC_APP_URL || process.env.NEXT_PUBLIC_VERCEL_URL || 'https://safevixai.com';

export const metadata: Metadata = {
  title: {
    template: '%s | SafeVixAI',
    default: 'SafeVixAI - AI-Powered Road Safety',
  },
  description:
    'Find nearest hospitals, police stations and ambulances instantly. AI chatbot for road laws and first aid. Works offline. IIT Madras Road Safety Hackathon 2026.',
  keywords: ['road safety', 'emergency', 'hospital finder', 'traffic laws', 'first aid', 'accident help', 'India'],
  authors: [{ name: 'SafeVixAI Team' }],
  manifest: '/manifest.json',
  appleWebApp: {
    statusBarStyle: 'black-translucent',
    title: 'SafeVixAI',
  },
  openGraph: {
    title: 'SafeVixAI - AI-Powered Road Safety',
    description: 'Emergency help, AI legal assistant and road reporter. Works offline.',
    type: 'website',
    siteName: 'SafeVixAI',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'SafeVixAI - AI-Powered Road Safety',
    description: 'Emergency help, AI legal assistant and road reporter. Works offline.',
  },
  robots: {
    index: true,
    follow: true,
  },
};

export const viewport: Viewport = {
  themeColor: [
    { media: '(prefers-color-scheme: dark)', color: '#0A0E14' },
    { media: '(prefers-color-scheme: light)', color: '#F0F4F8' },
  ],
  width: 'device-width',
  initialScale: 1,
  viewportFit: 'cover',
};

export default async function RootLayout({ children }: { children: React.ReactNode }) {
  const headerList = await headers();
  const locale = headerList.get('x-locale') || 'en';
  const isRtl = locale === 'ar' || locale === 'ur';

  const skipTextMap: Record<string, string> = {
    en: 'Skip to main content',
    hi: 'मुख्य सामग्री पर जाएं',
    ta: 'முக்கிய உள்ளடக்கத்திற்குச் செல்லவும்',
    te: 'ముఖ్యమైన సమాచారానికి వెళ్ళండి',
    kn: 'ಮುಖ್ಯ ವಿಷಯಕ್ಕೆ ಹೋಗಿ',
    ml: 'പ്രധാന ഉള്ളടക്കത്തിലേക്ക് പോകുക',
    mr: 'मुख्य मजकुराकडे जा',
    gu: 'મુખ્ય સામગ્રી પર જાઓ',
    bn: 'মূল বিষয়বস্তুতে যান',
    pa: 'ਮੁੱਖ ਸਮੱਗਰੀ ਤੇ ਜਾਓ',
    ur: 'بنیادی مواد پر جائیں',
    ar: 'انتقل إلى المحتوى الرئيسي',
    es: 'Saltar al contenido principal',
    fr: 'Passer au contenu principal',
  };
  const skipText = skipTextMap[locale] || skipTextMap.en;

  return (
    <html lang={locale} dir={isRtl ? 'rtl' : 'ltr'} suppressHydrationWarning className={`${inter.variable} ${spaceGrotesk.variable} ${jetbrainsMono.variable} font-sans`}>
      <head>
        <link rel="icon" type="image/png" href="/icons/favicon.png" />
        <link rel="apple-touch-icon" href="/icons/apple-touch-icon.png" />
        <link rel="preconnect" href="https://mt1.google.com" />
        <link rel="preconnect" href="https://api.maptiler.com" />
        <link rel="preconnect" href="https://tiles.openfreemap.org" />
        <link rel="preconnect" href={new URL(PUBLIC_API_BASE_URL).origin} />
        <link rel="preconnect" href={new URL(PUBLIC_CHATBOT_BASE_URL).origin} />
        <link rel="dns-prefetch" href="https://mt1.google.com" />
        <link rel="dns-prefetch" href="https://api.maptiler.com" />
        <link rel="dns-prefetch" href="https://tiles.openfreemap.org" />
        <link rel="dns-prefetch" href={new URL(PUBLIC_API_BASE_URL).origin} />
        <link rel="dns-prefetch" href={new URL(PUBLIC_CHATBOT_BASE_URL).origin} />
        <meta name="mobile-web-app-capable" content="yes" />

        {/* SEO Localization - Alternate Hreflang and Canonical URLs */}
        <link rel="canonical" href={`${BASE_URL}/${locale}`} />
        <link rel="alternate" href={`${BASE_URL}/en`} hrefLang="en" />
        <link rel="alternate" href={`${BASE_URL}/hi`} hrefLang="hi" />
        <link rel="alternate" href={`${BASE_URL}/ta`} hrefLang="ta" />
        <link rel="alternate" href={`${BASE_URL}/te`} hrefLang="te" />
        <link rel="alternate" href={`${BASE_URL}/kn`} hrefLang="kn" />
        <link rel="alternate" href={`${BASE_URL}/ml`} hrefLang="ml" />
        <link rel="alternate" href={`${BASE_URL}/mr`} hrefLang="mr" />
        <link rel="alternate" href={`${BASE_URL}/gu`} hrefLang="gu" />
        <link rel="alternate" href={`${BASE_URL}/bn`} hrefLang="bn" />
        <link rel="alternate" href={`${BASE_URL}/pa`} hrefLang="pa" />
        <link rel="alternate" href={`${BASE_URL}/ur`} hrefLang="ur" />
        <link rel="alternate" href={`${BASE_URL}/ar`} hrefLang="ar" />
        <link rel="alternate" href={`${BASE_URL}/es`} hrefLang="es" />
        <link rel="alternate" href={`${BASE_URL}/fr`} hrefLang="fr" />
        <link rel="alternate" href={BASE_URL} hrefLang="x-default" />

        {/* Flash-free theme init - runs before React hydration to prevent FOUC (via theme-init.js below) */}
        <Script src="/theme-init.js" strategy="beforeInteractive" />
      </head>
      <body>
        <a href="#main" className="sr-only focus:not-sr-only focus:fixed focus:top-4 focus:left-4 focus:z-[9999] focus:px-4 focus:py-2 focus:bg-brand-light focus:text-white focus:rounded-lg focus:text-sm focus:font-semibold focus:outline-none">
          {skipText}
        </a>
        <SentryInit />
        <AnalyticsProvider>
          <SWRConfig value={{
            dedupingInterval: 5000,
            focusThrottleInterval: 30000,
            revalidateOnFocus: false,
            revalidateOnReconnect: true,
            errorRetryCount: 3,
            errorRetryInterval: 2000,
          }}>
            <ThemeProvider>
            <GSAPProvider>
              <ConnectivityProvider>
                <EnterpriseClientAppHooks />
                <PwaUpdatePrompt />
                <AppFrame><ViewTransitions>{children}</ViewTransitions></AppFrame>
              <Toaster
                position="top-right"
                toastOptions={{
                  style: {
                    background: 'var(--surface-4)',
                    border: '1px solid var(--border-md)',
                    color: 'var(--text-1)',
                    fontFamily: 'var(--font-inter)',
                    fontSize: '13px',
                  },
                }}
              />
              </ConnectivityProvider>
            </GSAPProvider>
            </ThemeProvider>
          </SWRConfig>
        </AnalyticsProvider>
      </body>
    </html>
  );
}
