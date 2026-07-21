// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
import React from 'react';

import { useCallback, useRef } from 'react'

interface SwipeHandlers {
  onSwipeLeft?: () => void
  onSwipeRight?: () => void
  onSwipeUp?: () => void
  onSwipeDown?: () => void
}

const SWIPE_THRESHOLD = 50

export function useSwipe(handlers: SwipeHandlers) {
  const touchStart = useRef({ x: 0, y: 0 })

  const onTouchStart = useCallback((e: React.TouchEvent) => {
    touchStart.current = {
      x: e.touches[0].clientX,
      y: e.touches[0].clientY,
    }
  }, [])

  const onTouchEnd = useCallback((e: React.TouchEvent) => {
    const dx = e.changedTouches[0].clientX - touchStart.current.x
    const dy = e.changedTouches[0].clientY - touchStart.current.y

    if (Math.abs(dx) > Math.abs(dy)) {
      if (dx > SWIPE_THRESHOLD) handlers.onSwipeRight?.()
      if (dx < -SWIPE_THRESHOLD) handlers.onSwipeLeft?.()
    } else {
      if (dy > SWIPE_THRESHOLD) handlers.onSwipeDown?.()
      if (dy < -SWIPE_THRESHOLD) handlers.onSwipeUp?.()
    }
  }, [handlers])

  return { onTouchStart, onTouchEnd }
}
