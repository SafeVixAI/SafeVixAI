'use client'

import { useEffect, useRef } from 'react'
import { useAppStore } from '@/lib/store'
import { loadUserProfileFromIndexedDB, migrateUserProfileFromLocalStorage } from '@/lib/profile-storage'

export function useProfileHydration() {
  const cancelledRef = useRef(false)

  useEffect(() => {
    cancelledRef.current = false
    const hydrateProfile = async () => {
      await migrateUserProfileFromLocalStorage()
      const profile = await loadUserProfileFromIndexedDB()
      if (!cancelledRef.current) {
        if (profile) {
          useAppStore.getState().setUserProfile(profile)
        }
        useAppStore.getState().setProfileHydrated(true)
      }
    }
    void hydrateProfile()
    return () => {
      cancelledRef.current = true
    }
  }, [])
}
