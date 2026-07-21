'use client'

import { useEffect } from 'react'
import { fetchCsrfToken } from '@/lib/api'
import { PUBLIC_API_BASE_URL, PUBLIC_CHATBOT_BASE_URL } from '@/lib/public-env'

const PING_INTERVAL_MS = 540_000
const ENDPOINTS = [
  `${PUBLIC_API_BASE_URL}/health`,
  `${PUBLIC_CHATBOT_BASE_URL}/health`,
]

async function ping() {
  await Promise.allSettled(ENDPOINTS.map(url =>
    fetch(url, { method: 'GET', cache: 'no-store', mode: 'cors' })
  ))
}

export function useKeepAlivePing() {
  useEffect(() => {
    let intervalId: ReturnType<typeof setInterval> | null = null
    let terminated = false

    const startPinging = () => {
      ping()
      intervalId = setInterval(ping, PING_INTERVAL_MS)
    }

    const init = async () => {
      await fetchCsrfToken()
      if (!terminated) startPinging()
    }
    init()

    const onVisibility = () => {
      if (document.visibilityState === 'visible' && !terminated) {
        ping()
      }
    }
    document.addEventListener('visibilitychange', onVisibility)

    return () => {
      terminated = true
      if (intervalId) clearInterval(intervalId)
      document.removeEventListener('visibilitychange', onVisibility)
    }
  }, [])
}
