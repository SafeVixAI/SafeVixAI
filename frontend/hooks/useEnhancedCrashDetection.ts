'use client'

import { useState, useCallback, useEffect } from 'react'
import { toast } from 'sonner'
import { useShallow } from 'zustand/react/shallow'
import { useAppStore } from '@/lib/store'
import { FEATURES } from '@/lib/features'
import { STANDARD_GRAVITY_MS2 } from '@/lib/safety-constants'
import { useCrashDetection } from '@/hooks/useCrashDetection'
import { track } from '@/lib/analytics'

export interface CrashState {
  force: number
  severity: string
}

export function useEnhancedCrashDetection() {
  const crashDetectionEnabled = useAppStore(state => state.crashDetectionEnabled)
  const [crashState, setCrashState] = useState<CrashState | null>(null)

  const showIosPermissionToast = useCallback(() => {
    const isIOS = typeof window !== 'undefined' &&
      typeof DeviceMotionEvent !== 'undefined' &&
      typeof (DeviceMotionEvent as any).requestPermission === 'function'

    if (isIOS) {
      toast.info(
        "iOS Motion Sensors: Action required to enable automatic crash detection.",
        {
          position: "top-center",
          duration: 12000,
          action: {
            label: "Authorize",
            onClick: async () => {
              const { requestCrashPermission } = await import('@/lib/crash-detection')
              const granted = await requestCrashPermission()
              if (granted) {
                toast.success("Motion sensors authorized successfully!")
              } else {
                toast.error("Permission denied. Crash detection disabled.")
                useAppStore.getState().setCrashDetectionEnabled(false)
              }
            }
          }
        }
      )
    }
  }, [])

  const handleCrashDetected = useCallback((force: number) => {
    const gForce = force / STANDARD_GRAVITY_MS2
    const severity = gForce >= 15 ? 'severe' : gForce >= 10 ? 'moderate' : 'minor'
    track.crashDetected('impact', gForce)
    setCrashState({ force, severity })
  }, [])

  const clearCrashState = useCallback(() => {
    setCrashState(null)
  }, [])

  useEffect(() => {
    if (FEATURES.crashDetection && crashDetectionEnabled) {
      showIosPermissionToast()
    }
  }, [crashDetectionEnabled, showIosPermissionToast])

  const isEnabled = FEATURES.crashDetection && crashDetectionEnabled
  useCrashDetection({ onCrashDetected: handleCrashDetected, enabled: isEnabled })

  return { crashState, clearCrashState }
}
