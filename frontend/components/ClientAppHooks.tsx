// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
import React from 'react';

'use client'

import { useState, useEffect, useCallback } from 'react'
import { registerOfflineSyncListeners } from '@/lib/offline-sos-queue'
import { startCrashDetection, stopCrashDetection } from '@/lib/crash-detection'
import { STANDARD_GRAVITY_MS2 } from '@/lib/safety-constants'
import { toast } from 'sonner'
import { CrashCountdown } from '@/components/crash/CrashCountdown'

export function ClientAppHooks() {
 const [crashState, setCrashState] = useState<{
   force: number
   severity: string
 } | null>(null)

 const handleCancel = useCallback(() => {
   setCrashState(null)
   toast.info('SOS Cancelled', { duration: 3000 })
 }, [])

 const handleDispatch = useCallback(() => {
   setCrashState(null)
    toast.success('SOS dispatched to emergency contacts!', {
     duration: 8000,
   })
 }, [])

 useEffect(() => {
   registerOfflineSyncListeners()

   const handleCrashDetected = (force: number) => {
     const gForce = force / STANDARD_GRAVITY_MS2
     const severity = gForce >= 15 ? 'severe' : gForce >= 10 ? 'moderate' : 'minor'

     toast.error(
       <div className="flex flex-col gap-2">
          <p className="font-bold text-lg">CRASH DETECTED!</p>
         <p className="text-sm">G-Force Spike: {gForce.toFixed(1)}G</p>
       </div>,
       { duration: 5000, position: 'top-center' }
     )

     setCrashState({ force, severity })
   }

   void startCrashDetection(handleCrashDetected)
   return () => stopCrashDetection(handleCrashDetected)
 }, [])

 return (
   <>
     {crashState && (
       <CrashCountdown
         severity={crashState.severity}
         onCancel={handleCancel}
         onDispatch={handleDispatch}
       />
     )}
   </>
 )
}
