'use client'

import { useEffect } from 'react'
import type { Session } from '@supabase/supabase-js'
import { useAppStore } from '@/lib/store'
import { getSupabaseBrowserClient } from '@/lib/supabase-auth'

export function useSupabaseSession() {
  useEffect(() => {
    const supabase = getSupabaseBrowserClient()
    if (!supabase) return

    const syncSession = (session: Session | null) => {
      const store = useAppStore.getState()
      if (!session?.access_token) {
        store.clearAuth()
        return
      }
      const displayName =
        (session.user.user_metadata?.name as string | undefined) ||
        session.user.email ||
        'SafeVixAI User'
      store.setAuth(displayName)
      store.setUserProfile({ name: displayName })
    }

    void supabase.auth.getSession().then(({ data }) => syncSession(data.session))
    const { data } = supabase.auth.onAuthStateChange((_event, session) => {
      syncSession(session)
    })

    return () => data.subscription.unsubscribe()
  }, [])
}
