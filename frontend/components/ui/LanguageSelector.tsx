'use client';

// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team


import React from 'react'
import { Globe } from 'lucide-react'
import { useRouter } from 'next/navigation'
import { useShallow } from 'zustand/react/shallow'
import { useAppStore } from '@/lib/store'
import { cn } from '@/lib/utils'

const languages = [
  { value: 'en', label: 'English' },
  { value: 'hi', label: 'हिन्दी (Hindi)' },
  { value: 'ta', label: 'தமிழ் (Tamil)' },
  { value: 'te', label: 'తెలుగు (Telugu)' },
  { value: 'kn', label: 'ಕನ್ನಡ (Kannada)' },
  { value: 'ml', label: 'മലയാളം (Malayalam)' },
  { value: 'mr', label: 'मराठी (Marathi)' },
  { value: 'gu', label: 'ગુજરાતી (Gujarati)' },
  { value: 'bn', label: 'বাংলা (Bengali)' },
  { value: 'pa', label: 'ਪੰਜਾਬੀ (Punjabi)' },
  { value: 'ur', label: 'اردو (Urdu)' },
  { value: 'ar', label: 'العربية (Arabic)' },
  { value: 'es', label: 'Español (Spanish)' },
  { value: 'fr', label: 'Français (French)' },
]

interface LanguageSelectorProps {
  className?: string
  onChangeLanguage?: (_lang: string) => void
}

export function LanguageSelector({ className, onChangeLanguage }: LanguageSelectorProps) {
  const router = useRouter()
  const { userProfile, setUserProfile } = useAppStore(useShallow((state) => ({
    userProfile: state.userProfile,
    setUserProfile: state.setUserProfile,
  })))

  const currentLang = userProfile.preferredLanguage || 'en'

  const handleLanguageChange = (val: string) => {
    setUserProfile({ preferredLanguage: val })
    if (onChangeLanguage) {
      onChangeLanguage(val)
    }

    if (typeof window !== 'undefined') {
      const pathname = window.location.pathname
      const search = window.location.search
      const pathParts = pathname.split('/')
      const firstSegment = pathParts[1]
      
      const SUPPORTED_LOCALES = [
        'en', 'hi', 'ta', 'te', 'kn', 'ml', 'mr', 'gu', 'bn', 'pa', 'ur',
        'ar', 'es', 'fr'
      ]
      
      if (SUPPORTED_LOCALES.includes(firstSegment)) {
        pathParts[1] = val
      } else {
        pathParts.splice(1, 0, val)
      }
      
      const newPathname = pathParts.join('/')
      const targetUrl = newPathname + search
      
      router.push(targetUrl)
    }
  }

  return (
    <div className={cn("relative inline-block w-full text-left", className)}>
      <div className="relative flex items-center">
        <Globe size={18} className="absolute left-3 text-brand-light pointer-events-none" />
        <select
          value={currentLang}
          onChange={(e) => handleLanguageChange(e.target.value)}
          aria-label="Select preferred language"
          className={cn(
            'w-full appearance-none rounded-xl border px-3 py-2.5 pl-10 pr-10 text-sm text-text-1 transition-all outline-none',
            'bg-surface-2/65 backdrop-blur-md border-border/40 focus:border-brand-light/50 focus:ring-3 focus:ring-brand-light/12',
            'hover:bg-surface-3/50 hover:border-brand-light/30 cursor-pointer font-medium font-sans'
          )}
        >
          {languages.map((lang) => (
            <option 
              key={lang.value} 
              value={lang.value}
              className="bg-surface-1 text-text-1 py-2"
            >
              {lang.label}
            </option>
          ))}
        </select>
        <div className="pointer-events-none absolute right-3 flex items-center text-text-3">
          <svg className="h-4 w-4 fill-current" viewBox="0 0 20 20">
            <path d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" />
          </svg>
        </div>
      </div>
    </div>
  )
}