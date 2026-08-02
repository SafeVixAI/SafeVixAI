// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

function requiredPublicUrl(name: string, value: string | undefined, fallback: string): string {
  const normalized = value?.trim().replace(/\/+$/, '');
  if (!normalized) {
    if (typeof process !== 'undefined' && process.env.NODE_ENV !== 'test') {
      console.warn(`SafeVixAI: ${name} is not set. Using fallback: ${fallback}`);
    }
    return fallback;
  }
  return normalized;
}

export const PUBLIC_API_BASE_URL = requiredPublicUrl(
  'NEXT_PUBLIC_API_URL or NEXT_PUBLIC_BACKEND_URL',
  process.env.NEXT_PUBLIC_API_URL || process.env.NEXT_PUBLIC_BACKEND_URL,
  'https://safevixai-api.onrender.com',
);

export const PUBLIC_CHATBOT_BASE_URL = requiredPublicUrl(
  'NEXT_PUBLIC_CHATBOT_URL',
  process.env.NEXT_PUBLIC_CHATBOT_URL,
  'https://safevixai-chatbot.onrender.com',
);

export function publicApiWebSocketUrl(path: string): string {
  const base = new URL(PUBLIC_API_BASE_URL);
  base.protocol = base.protocol === 'https:' ? 'wss:' : 'ws:';
  const target = new URL(path.startsWith('/') ? path : `/${path}`, base.origin);
  base.pathname = target.pathname;
  base.search = target.search;
  base.hash = '';
  return base.toString();
}
