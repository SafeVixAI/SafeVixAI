'use client'

import { useEffect } from 'react'
import i18n from '@/lib/i18n'

const SUPPORTED_LOCALES = [
  'en', 'hi', 'ta', 'te', 'kn', 'ml', 'mr', 'gu', 'bn', 'pa', 'ur',
  'ar', 'es', 'fr'
]

export function useI18nClientSync(preferredLanguage?: string) {
  useEffect(() => {
    if (typeof window === 'undefined') return
    const pathParts = window.location.pathname.split('/')
    const pathLocale = pathParts[1]
    const preferred = preferredLanguage || 'en'
    const targetLocale = SUPPORTED_LOCALES.includes(pathLocale) ? pathLocale : preferred

    if (i18n.language !== targetLocale) {
      i18n.changeLanguage(targetLocale).then(() => {
        const isRtl = targetLocale === 'ar' || targetLocale === 'ur'
        document.documentElement.dir = isRtl ? 'rtl' : 'ltr'
        document.documentElement.lang = targetLocale
      })
    }
  }, [preferredLanguage])
}
