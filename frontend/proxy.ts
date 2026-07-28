// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export const config = {
  matcher: [
    '/((?!_next|api|icons|offline-data|leaflet|sw\\.js|.*\\..*).*)',
  ],
};

const SUPPORTED_LOCALES = [
  'en', 'hi', 'ta', 'te', 'kn', 'ml', 'mr', 'gu', 'bn', 'pa', 'ur',
  'ar', 'fr', 'es'
];
const DEFAULT_LOCALE = 'en';

function detectLocale(request: NextRequest): string {
  const cookieLocale = request.cookies.get('svai-locale')?.value;
  if (cookieLocale && SUPPORTED_LOCALES.includes(cookieLocale)) {
    return cookieLocale;
  }
  const acceptLang = request.headers.get('accept-language');
  if (acceptLang) {
    const matched = acceptLang
      .split(',')
      .map((lang) => lang.split(';')[0].trim().substring(0, 2))
      .find((lang) => SUPPORTED_LOCALES.includes(lang));
    if (matched) return matched;
  }
  return DEFAULT_LOCALE;
}

function setLocaleHeaders(response: NextResponse, locale: string): void {
  response.headers.set('x-locale', locale);
  response.cookies.set('svai-locale', locale, {
    path: '/',
    maxAge: 365 * 24 * 60 * 60,
    sameSite: 'lax',
  });
}

function buildCSP(nonce: string): string {
  const backendOrigins = [];
  const apiUrl = process.env.NEXT_PUBLIC_BACKEND_URL;
  const chatbotUrl = process.env.NEXT_PUBLIC_CHATBOT_URL;
  for (const value of [apiUrl, chatbotUrl].filter(Boolean)) {
    try {
      const url = new URL(value!);
      backendOrigins.push(`${url.protocol}//${url.host}`);
      backendOrigins.push(`${url.protocol === 'https:' ? 'wss:' : 'ws:'}//${url.host}`);
    } catch { /* skip invalid urls */ }
  }

  const externalApis = [
    'https://api.tomtom.com',
    'https://api.bigdatacloud.net',
    'https://router.project-osrm.org',
    'https://countriesnow.space',
    'https://photon.komoot.io',
    'https://app.posthog.com',
    'https://tiles.openfreemap.org',
    'https://mt1.google.com',
    'https://api.maptiler.com',
    'https://api.what3words.com',
    'https://*.tile.openstreetmap.org',
    'https://demotiles.maplibre.org',
    'https://tiles.stadiamaps.com',
    ...(process.env.NEXT_PUBLIC_SUPABASE_URL ? [process.env.NEXT_PUBLIC_SUPABASE_URL.trim()] : []),
  ];

  const isDev = process.env.NODE_ENV !== 'production';
  const devConnect = isDev ? ["http://localhost:*", "http://127.0.0.1:*", "ws://localhost:*", "ws://127.0.0.1:*"] : [];

  return [
    "default-src 'self'",
    `script-src 'self' 'nonce-${nonce}' 'wasm-unsafe-eval'${isDev ? " 'unsafe-eval'" : ''} https://cdn.jsdelivr.net`,
    "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
    "img-src 'self' data: https:",
    "font-src 'self' data: https://fonts.gstatic.com",
    `connect-src 'self' ${[...backendOrigins, ...externalApis, ...devConnect].join(' ')}`,
    "worker-src 'self' blob:",
    "child-src 'self' blob:",
    "frame-ancestors 'none'",
    "base-uri 'self'",
    "form-action 'self'",
    "object-src 'none'",
  ].join('; ');
}

export function proxy(request: NextRequest) {
  const { pathname, search } = request.nextUrl;

  // Skip non-page routes early
  if (
    pathname.startsWith('/_next') ||
    pathname.startsWith('/api') ||
    pathname.startsWith('/icons') ||
    pathname.startsWith('/offline-data') ||
    pathname.startsWith('/leaflet') ||
    pathname.includes('.') ||
    pathname === '/sw.js'
  ) {
    return NextResponse.next();
  }

  const nonce = crypto.randomUUID();
  const locale = detectLocale(request);

  const pathParts = pathname.split('/');
  const firstSegment = pathParts[1];
  const hasLocale = SUPPORTED_LOCALES.includes(firstSegment);

  let response: NextResponse;

  if (hasLocale) {
    const actualPathname = '/' + pathParts.slice(2).join('/');
    const rewriteUrl = new URL(actualPathname === '/' ? '/' : actualPathname, request.url);
    rewriteUrl.search = search;
    response = NextResponse.rewrite(rewriteUrl);
  } else {
    response = NextResponse.next();
  }

  response.headers.set('x-nonce', nonce);
  response.headers.set('Content-Security-Policy', buildCSP(nonce));
  setLocaleHeaders(response, hasLocale ? firstSegment : locale);

  return response;
}
