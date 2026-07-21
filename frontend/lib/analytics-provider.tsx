'use client';

// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
import React from 'react';


import { useEffect, useState, useRef } from 'react'
import { useAppStore } from './store'
import { logClientWarning } from './client-logger'
import { initAnalyticsClient } from './analytics'

export const ANALYTICS_CONSENT_KEY = 'safevixai:analytics-consent'

export function AnalyticsProvider({ children }: { children: React.ReactNode }) {
  const analyticsOptIn = useAppStore((s) => s.analyticsOptIn)
  const [posthogReady, setPosthogReady] = useState(false)
  const [PostHogProvider, setPostHogProvider] = useState<React.ComponentType<{ client: any; children: React.ReactNode }> | null>(null)
  const [posthogClient, setPosthogClient] = useState<any>(null)
  const initRef = useRef(false)

  useEffect(() => {
    if (initRef.current) return

    const consent = window.localStorage.getItem(ANALYTICS_CONSENT_KEY)
    const optedIn = consent === 'granted' || analyticsOptIn

    if (!optedIn) {
      setPosthogReady(true)
      return
    }

    const posthogKey = process.env.NEXT_PUBLIC_POSTHOG_KEY
    const posthogHost = process.env.NEXT_PUBLIC_POSTHOG_HOST || 'https://app.posthog.com'

    if (!posthogKey) {
      logClientWarning('PostHog is not initialized (NEXT_PUBLIC_POSTHOG_KEY missing)')
      setPosthogReady(true)
      return
    }

    initRef.current = true

    Promise.all([
      import('posthog-js'),
      import('posthog-js/react'),
    ]).then(([ph, react]) => {
      const posthog = ph.default
      posthog.init(posthogKey, {
        api_host: posthogHost,
        capture_pageview: false,
        capture_pageleave: true,
        autocapture: false,
        disable_session_recording: true,
      })
      initAnalyticsClient(posthog)
      setPosthogClient(posthog)
      setPostHogProvider(() => react.PostHogProvider)
      setPosthogReady(true)
    })
  }, [analyticsOptIn])

  if (!posthogReady) return <>{children}</>
  if (!PostHogProvider || !posthogClient) return <>{children}</>
  return <PostHogProvider client={posthogClient}>{children}</PostHogProvider>
}