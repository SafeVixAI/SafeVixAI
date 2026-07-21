'use client'

import { useEffect } from 'react'
import { initRUM } from '@/lib/rum'
import { registerOfflineSyncListeners } from '@/lib/offline-sos-queue'
import { logClientError } from '@/lib/client-logger'

function registerSW() {
  if (typeof window === 'undefined' || !('serviceWorker' in navigator)) return
  const doRegister = () => {
    navigator.serviceWorker.register('/sw.js')
      .then((reg) => {
        if (process.env.NODE_ENV !== 'production') console.log('SafeVixAI: ServiceWorker registered successfully:', reg.scope)
        if (navigator.storage && navigator.storage.persist) {
          navigator.storage.persist().then((persistent) => {
            if (persistent && process.env.NODE_ENV !== 'production') {
              console.log('SafeVixAI: Persistent storage granted by browser.')
            }
          }).catch(() => {})
        }
      })
      .catch((err) => {
        logClientError('ServiceWorker registration failed', err)
      })
  }
  if (document.readyState === 'complete') {
    doRegister()
  } else {
    window.addEventListener('load', doRegister, { once: true })
  }
}

export function useClientServiceWorker() {
  useEffect(() => {
    initRUM()
    registerOfflineSyncListeners()
    registerSW()
  }, [])
}
