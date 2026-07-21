'use client';

import React from 'react'

import { useEffect, useState, useRef, useCallback } from 'react'
import { toast } from 'sonner'
import { useShallow } from 'zustand/react/shallow'
import { useAppStore } from '@/lib/store'
import { triggerSos } from '@/lib/api'
import { enqueueSOS } from '@/lib/offline-sos-queue'
import { track } from '@/lib/analytics'
import { beginLocationBroadcast, startFamilyTracking } from '@/lib/live-tracking'
import { PUBLIC_CHATBOT_BASE_URL } from '@/lib/public-env'
import { Loader2 } from 'lucide-react'
import { useI18nClientSync } from '@/hooks/useI18nClientSync'
import { useClientServiceWorker } from '@/hooks/useClientServiceWorker'
import { useProfileHydration } from '@/hooks/useProfileHydration'
import { useSupabaseSession } from '@/hooks/useSupabaseSession'
import { useKeepAlivePing } from '@/hooks/useKeepAlivePing'
import { usePageLoadTiming } from '@/hooks/usePageLoadTiming'
import { useEnhancedCrashDetection } from '@/hooks/useEnhancedCrashDetection'
import { CrashCountdown } from '@/components/crash/CrashCountdown'
import InstallPrompt from '@/components/InstallPrompt'
import CookieConsent from '@/components/ui/CookieConsent'
import GpsConsent from '@/components/ui/GpsConsent'

function SystemBanners() {
  const connectivity = useAppStore(state => state.connectivity)
  const [localWarming, setLocalWarming] = useState(false)
  const setServerWarming = useAppStore(state => state.setServerWarming)

  const skipAuth = process.env.NODE_ENV !== 'production' &&
    typeof window !== 'undefined' &&
    window.localStorage.getItem('__E2E_SKIP_AUTH__') === 'true';

  useEffect(() => {
    if (skipAuth) return;
    const checkHealth = async () => {
      try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 2000);
        const res = await fetch(`${PUBLIC_CHATBOT_BASE_URL}/speech/status`, { signal: controller.signal });
        clearTimeout(timeoutId);
        if (!res.ok) throw new Error('Not ready');
        setLocalWarming(false);
        setServerWarming(false);
      } catch (err) {
        if ((err as Error).name === 'AbortError') {
          setLocalWarming(true);
          setServerWarming(true);
        }
      }
    };
    checkHealth();
  }, [setServerWarming, skipAuth]);

  return (
    <>
      {localWarming && connectivity !== 'offline' && (
        <div className="fixed top-0 left-0 w-full z-[9999] bg-brand text-white text-xs font-bold px-4 py-1.5 flex items-center justify-center gap-2 shadow-md">
          <Loader2 size={14} className="animate-spin" />
          CONNECTING... (~30 SECONDS ON FIRST LOAD)
        </div>
      )}
    </>
  )
}

export function EnterpriseClientAppHooks() {
  const { gpsLocation, userProfile } = useAppStore(useShallow((state) => ({
    gpsLocation: state.gpsLocation,
    userProfile: state.userProfile,
  })))

  useI18nClientSync(userProfile.preferredLanguage)
  useClientServiceWorker()
  useProfileHydration()
  useSupabaseSession()
  useKeepAlivePing()
  usePageLoadTiming()
  const { crashState, clearCrashState } = useEnhancedCrashDetection()

  const [dispatching, setDispatching] = useState(false)
  const stopCrashTrackingRef = useRef<(() => void) | null>(null)

  const handleDispatchSos = useCallback(async () => {
    if (dispatching) return
    if (!gpsLocation) {
      toast.error('Crash detected, but location is unavailable. Open SOS and share your location manually.', {
        duration: 0,
        position: 'top-center',
      })
      clearCrashState()
      return
    }

    setDispatching(true)
    try {
      track.sosActivated('crash_detection')
      await triggerSos({ lat: gpsLocation.lat, lon: gpsLocation.lon })
      if (userProfile.name.trim()) {
        try {
          const trackingSession = await startFamilyTracking({
            userName: userProfile.name,
            bloodGroup: userProfile.bloodGroup || undefined,
            vehicleNumber: userProfile.vehicleNumber || undefined,
            latitude: gpsLocation.lat,
            longitude: gpsLocation.lon,
          })
          stopCrashTrackingRef.current?.()
          stopCrashTrackingRef.current = beginLocationBroadcast(trackingSession.session_id)
          toast.success(`Family tracking started: ${trackingSession.tracking_url}`, {
            duration: 0,
            position: 'top-center',
          })
        } catch {
          toast.error('Auto-SOS sent, but family tracking could not be started. Open SOS to share manually.', {
            duration: 0,
            position: 'top-center',
          })
        }
      }
      toast.success('SOS sent to emergency contacts - they can track you now.', {
        duration: 0,
        position: 'top-center',
      })
    } catch {
      track.offlineSosQueued()
      await enqueueSOS({ lat: gpsLocation.lat, lon: gpsLocation.lon })
      toast.error('Network unavailable - SOS saved offline and will retry automatically.', {
        duration: 0,
        position: 'top-center',
      })
    } finally {
      setDispatching(false)
      clearCrashState()
    }
  }, [dispatching, gpsLocation, userProfile, clearCrashState])

  return (
    <>
      <SystemBanners />
      {crashState && (
        <CrashCountdown
          severity={crashState.severity}
          onCancel={() => {
            track.crashCancelled(0)
            clearCrashState()
          }}
          onDispatch={handleDispatchSos}
        />
      )}
      <InstallPrompt />
      <CookieConsent />
      <GpsConsent />
    </>
  )
}
