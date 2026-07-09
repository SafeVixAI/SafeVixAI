'use client'

import { useEffect } from 'react'
import { track } from '@/lib/analytics'

export function usePageLoadTiming() {
  useEffect(() => {
    if (typeof window === 'undefined') return
    if (document.readyState === 'complete') {
      track.pageLoadTiming()
    } else {
      window.addEventListener('load', () => track.pageLoadTiming(), { once: true })
    }
  }, [])
}
