'use client';

// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team


import React, { useState, useEffect, memo } from 'react';
import Link from 'next/link';
import { Menu, Mic, MapPin, Moon, Sun, Monitor, Search, ArrowLeft, Layers, Hospital, Shield, Ambulance, Flame, Pill } from 'lucide-react';
import { formatAccuracyLabel, formatLocationLabel, isApproximateLocation } from '@/lib/location-utils';
import { useShallow } from 'zustand/react/shallow';
import { useAppStore } from '@/lib/store';
import { useTheme } from '@/components/ThemeProvider';
import { searchPlaces, GeocodingResult } from '@/lib/geocoding';
import { useDebouncedCallback } from 'use-debounce';

interface TopSearchProps {
  isMapPage?: boolean;
  forceShow?: boolean;
  showBack?: boolean;
  backHref?: string;
}

const MAP_FILTER_CHIPS: Array<{
  label: string;
  value: 'all' | 'hospital' | 'police' | 'ambulance' | 'fire' | 'pharmacy';
  icon: React.ReactNode;
  color: string;
  bg: string;
}> = [
  { label: 'All', value: 'all', icon: <Layers size={16} strokeWidth={2.5} />, color: 'text-text-2', bg: 'bg-surface-3' },
  { label: 'Hospitals', value: 'hospital', icon: <Hospital size={16} strokeWidth={2.5} />, color: 'text-emergency', bg: 'bg-emergency/10' },
  { label: 'Police', value: 'police', icon: <Shield size={16} strokeWidth={2.5} />, color: 'text-brand-light', bg: 'bg-brand/10' },
  { label: 'Ambulance', value: 'ambulance', icon: <Ambulance size={16} strokeWidth={2.5} />, color: 'text-text-green', bg: 'bg-brand/10' },
  { label: 'Fire', value: 'fire', icon: <Flame size={16} strokeWidth={2.5} />, color: 'text-text-amber', bg: 'bg-text-amber/10' },
  { label: 'Pharmacy', value: 'pharmacy', icon: <Pill size={16} strokeWidth={2.5} />, color: 'text-cyan-500', bg: 'bg-cyan-500/10' },
];

const TopSearch = memo(function TopSearch({ 
  isMapPage = false, 
  forceShow = false,
  showBack = false,
  backHref = '/'
}: TopSearchProps) {
  const { gpsError, gpsLocation, serviceCategory, setMapSearchTarget, setServiceCategory, setSystemSidebarOpen, isDesktopSidebarCollapsed, setDesktopSidebarCollapsed, isThinSidebarEnabled } = useAppStore(useShallow((state) => ({
    gpsError: state.gpsError,
    gpsLocation: state.gpsLocation,
    serviceCategory: state.serviceCategory,
    setMapSearchTarget: state.setMapSearchTarget,
    setServiceCategory: state.setServiceCategory,
    setSystemSidebarOpen: state.setSystemSidebarOpen,
    isDesktopSidebarCollapsed: state.isDesktopSidebarCollapsed,
    setDesktopSidebarCollapsed: state.setDesktopSidebarCollapsed,
    isThinSidebarEnabled: state.isThinSidebarEnabled,
  })));
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);
  const [isFocused, setIsFocused] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [results, setResults] = useState<GeocodingResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const debouncedSearch = useDebouncedCallback(async (query: string) => {
    setIsSearching(true);
    const res = await searchPlaces(query);
    setResults(res);
    setIsSearching(false);
  }, 400);

  useEffect(() => {
    if (!searchQuery.trim() || searchQuery.length < 2) {
      setResults([]);
      setIsSearching(false);
      debouncedSearch.cancel();
      return;
    }
    debouncedSearch(searchQuery);
  }, [searchQuery, debouncedSearch]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (results.length > 0) {
      selectResult(results[0]);
    }
  };

  const selectResult = (r: GeocodingResult) => {
    setMapSearchTarget({
      lat: r.lat,
      lon: r.lon,
      label: r.label || r.name,
      city: r.city || undefined,
      state: r.state || undefined,
      timestamp: Date.now(),
    });
    window.dispatchEvent(new CustomEvent('svai:fly-to', { detail: { lat: r.lat, lng: r.lon } }));
    setIsFocused(false);
    setSearchQuery(r.name || r.label);
    setResults([]);
  };

  const locationLabel = formatLocationLabel(gpsLocation, gpsError);
  const locationAccuracy = formatAccuracyLabel(gpsLocation);
  const locationIsApproximate = isApproximateLocation(gpsLocation);

  const requestLocation = () => {
    setMapSearchTarget(null);
    window.dispatchEvent(new CustomEvent('svai:refresh-location'));
  };

  return (
    <div className={`absolute top-0 left-0 w-full z-40 px-4 pb-2 pt-[calc(0.75rem+env(safe-area-inset-top))] md:pb-6 md:pt-[calc(1.5rem+env(safe-area-inset-top))] pointer-events-none flex flex-col items-center ${(!isMapPage && !forceShow) ? 'lg:hidden' : ''}`}>
      
      {/* Top Row: Search Bar (Center) & Desktop Controls */}
      <div
        className="w-full flex items-center justify-center md:justify-between lg:justify-center relative md:gap-4 lg:gap-6 md:px-4 lg:px-0"
      >
        
        {/* Left Side: Location Badge on Tablet/Desktop (Hidden on short landscape) */}
        <div className="hidden min-[1100px]:flex pointer-events-auto h-[52px] shrink-0">
          <button
            type="button"
            onClick={requestLocation}
            title={gpsError ?? 'Refresh current location'}
            className="flex items-center h-full gap-2 bg-surface-1/95 dark:bg-surface-2/95 backdrop-blur-2xl ring-0 shadow-[0_8px_30px_rgb(0,0,0,0.12)] dark:shadow-[0_8px_30px_rgb(0,0,0,0.4)] rounded-full px-5 hover:bg-surface-2 dark:hover:bg-surface-3 transition-all cursor-pointer group"
          >
            <div className="bg-success/10 p-1.5 rounded-full">
              <MapPin className="w-4 h-4 text-success" />
            </div>
            <span className="text-sm font-bold text-text-1 group-hover:text-success transition-colors whitespace-nowrap truncate max-w-[200px]">
              {locationLabel}
            </span>
            {locationAccuracy ? (
              <span className={`hidden min-[1320px]:inline text-[10px] font-semibold uppercase tracking-[0.18em] ${locationIsApproximate ? 'text-warning' : 'text-text-3'}`}>
                {locationAccuracy}
              </span>
            ) : null}
          </button>
        </div>

        {/* Floating Pill Search Bar (Google Maps Style) */}
        <form 
          onSubmit={handleSearch}
          role="search"
          aria-label="Search"
          className={`w-full sm:max-w-md md:max-w-none md:flex-1 lg:flex-none lg:w-full lg:max-w-xl pointer-events-auto flex items-center h-[52px] bg-surface-1/95 dark:bg-surface-2/95 backdrop-blur-2xl rounded-full px-4 transition-all duration-300 border ${isFocused ? 'border-brand/50 shadow-sm ring-1 ring-brand/20' : 'border-transparent shadow-[0_8px_30px_rgb(0,0,0,0.12)] dark:shadow-[0_8px_30px_rgb(0,0,0,0.4)]'}`}
        >
          
          {showBack && (
            <Link href={backHref} className="p-2 mr-1 rounded-full hover:bg-black/5 dark:hover:bg-white/10 active:scale-95 transition-all text-text-1 lg:hidden group flex items-center justify-center">
              <ArrowLeft className="w-6 h-6 group-hover:-translate-x-0.5 transition-transform" />
            </Link>
          )}

          <button 
            type="button"
            onClick={() => setSystemSidebarOpen(true)}
            aria-label="Open navigation menu"
            className="p-2 rounded-full hover:bg-black/5 dark:hover:bg-white/10 active:scale-95 transition-all text-text-1 lg:hidden mr-1"
          >
            <Menu className="w-6 h-6" />
          </button>

          {isDesktopSidebarCollapsed && !isThinSidebarEnabled ? (
            <button 
              type="button"
              onClick={() => setDesktopSidebarCollapsed(false)}
              aria-label="Expand sidebar"
              className="p-2 rounded-full hover:bg-black/5 dark:hover:bg-white/10 active:scale-95 transition-all text-text-1 hidden lg:block mr-1"
            >
              <Menu className="w-6 h-6" />
            </button>
          ) : (
            <div className="p-2 hidden lg:flex items-center justify-center text-text-2 mr-1">
              <Search className="w-5 h-5" />
            </div>
          )}

          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Ask Maps or Search"
            aria-label="Search input"
            onFocus={() => setIsFocused(true)}
            onBlur={() => setIsFocused(false)}
            className="flex-1 bg-transparent border-none outline-none focus:outline-none focus:ring-0 focus-visible:ring-0 px-2 text-text-1 placeholder:text-text-3 font-medium text-base h-full w-full"
          />

          <button type="button" aria-label="Voice search" className="p-2 rounded-full bg-brand/10 text-brand hover:bg-brand/20 active:scale-95 transition-all ml-2">
            <Mic className="w-5 h-5" />
          </button>
          
          {/* Autocomplete Dropdown */}
          {isFocused && (searchQuery.length > 1 || results.length > 0) && (
            <div className="absolute top-[calc(100%+8px)] left-0 w-full bg-surface-1 dark:bg-surface-2 rounded-lg shadow-xl border border-border overflow-hidden z-50">
              {isSearching && results.length === 0 ? (
                <div className="p-4 text-center text-sm text-text-2">Searching...</div>
              ) : results.length > 0 ? (
                <ul>
                  {results.map((r, i) => (
                    <li key={i}>
                      <button
                        type="button"
                        onClick={() => selectResult(r)}
                        className="w-full text-left px-4 py-3 hover:bg-surface-3 transition-colors flex flex-col border-b border-border last:border-0"
                      >
                        <span className="font-semibold text-text-1">{r.name}</span>
                        <span className="text-xs text-text-3">{r.label}</span>
                      </button>
                    </li>
                  ))}
                </ul>
              ) : searchQuery.length > 2 && !isSearching ? (
                <div className="p-4 text-center text-sm text-text-2">No places found in India.</div>
              ) : null}
            </div>
          )}
        </form>

        {/* Right Side: Theme Toggle on Tablet/Desktop */}
        <div className="hidden md:flex pointer-events-auto h-[52px]">
          {mounted && (
            <div className="flex items-center h-full gap-1 bg-surface-1/90 dark:bg-surface-2/90 backdrop-blur-xl ring-1 ring-border shadow-2xl rounded-full px-1.5">
              <button 
                onClick={() => setTheme('light')}
                className={`p-2 rounded-full transition-all ${theme === 'light' ? 'bg-brand/15 text-brand' : 'text-text-3 hover:text-text-1'}`}
                aria-label="Switch to light theme"
              >
                <Sun className="w-5 h-5" />
              </button>
              <button 
                onClick={() => setTheme('dark')}
                className={`p-2 rounded-full transition-all ${theme === 'dark' ? 'bg-brand/15 text-brand' : 'text-text-3 hover:text-text-1'}`}
                aria-label="Switch to dark theme"
              >
                <Moon className="w-5 h-5" />
              </button>
              <button 
                onClick={() => setTheme('system')}
                className={`p-2 rounded-full transition-all ${theme === 'system' ? 'bg-brand/15 text-brand' : 'text-text-3 hover:text-text-1'}`}
                aria-label="Switch to system theme"
              >
                <Monitor className="w-5 h-5" />
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Floating Chips Row */}
      {isMapPage && (
        <div
          className="mt-3 overflow-x-auto w-full [&::-webkit-scrollbar]:hidden [-ms-overflow-style:none] [scrollbar-width:none] pointer-events-auto"
        >
          <div className="flex items-center gap-2 px-1 w-max mx-auto">
            <button
              type="button"
              onClick={requestLocation}
              aria-label={gpsError ?? 'Refresh current location'}
              className="min-[1100px]:hidden flex items-center gap-2 px-3 py-1.5 bg-surface-1/90 dark:bg-surface-2/90 backdrop-blur-xl rounded-full shadow-lg ring-1 ring-border whitespace-nowrap active:scale-95 transition-transform hover:shadow-2xl"
            >
              <div className="bg-success/10 p-1 rounded-full flex items-center justify-center">
                <MapPin className="h-4 w-4 text-success" />
              </div>
              <span className="text-sm font-semibold text-text-1 truncate max-w-[200px]">
                {gpsError ? 'Enable Location' : gpsLocation ? 'Refresh Location' : 'Use My Location'}
              </span>
              {locationIsApproximate && locationAccuracy ? (
                <span className="text-[10px] font-semibold uppercase tracking-[0.16em] text-warning">
                  {locationAccuracy}
                </span>
              ) : null}
            </button>
            {MAP_FILTER_CHIPS.map((chip) => {
              const isActive = serviceCategory === chip.value;
              return (
              <button
                key={chip.label}
                onClick={() => setServiceCategory(chip.value)}
                className={`flex items-center gap-2 px-3 py-1.5 bg-surface-2/90 backdrop-blur-xl rounded-full shadow-lg ring-1 whitespace-nowrap active:scale-95 transition-transform hover:shadow-2xl ${isActive ? 'ring-2 ring-brand/30' : 'ring-border'}`}
                data-active={isActive}
                aria-pressed={isActive}
              >
                <div className={`${isActive ? 'bg-brand/15' : chip.bg} p-1 rounded-full flex items-center justify-center ${isActive ? 'text-brand' : chip.color}`}>
                  {chip.icon}
                </div>
                <span className={`text-sm font-semibold ${isActive ? 'text-brand' : 'text-text-1'}`}>
                  {chip.label}
                </span>
              </button>
            )})}
          </div>
        </div>
      )}

    </div>
  );
});

export default TopSearch;