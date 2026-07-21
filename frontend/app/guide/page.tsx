'use client';

// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team


import React, { useEffect, useState, useMemo, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Search,
  MapPin,
  Loader2,
  Building2,
  Filter,
  Navigation,
} from 'lucide-react';
import { TerminalHeader } from '@/components/ui/TerminalHeader';
import { MunicipalityCard } from '@/components/guide/MunicipalityCard';
import type { Municipality } from '@/lib/api';
import { fetchMunicipalities, fetchNearbyMunicipalities } from '@/lib/api';

const STATE_CHIPS = [
  'MH', 'TN', 'AP', 'KA', 'TS', 'DL', 'WB', 'UP', 'GJ', 'RJ', 'MP', 'KL', 'BR', 'PB',
] as const;

const TYPE_FILTERS = [
  { labelKey: 'guide.all', defaultLabel: 'All', value: '' },
  { labelKey: 'guide.corporation', defaultLabel: 'Corporation', value: 'municipal_corporation' },
  { labelKey: 'guide.municipality', defaultLabel: 'Municipality', value: 'municipality' },
] as const;

export default function GuidePage() {
  const { t } = useTranslation('common');
  const [municipalities, setMunicipalities] = useState<Municipality[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedState, setSelectedState] = useState('');
  const [selectedType, setSelectedType] = useState('');
  const [nearbyMode, setNearbyMode] = useState(false);
  const [locating, setLocating] = useState(false);
  const [showFilters, setShowFilters] = useState(false);

  // Load data: try API first, fallback to offline bundle
  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetchMunicipalities({ pageSize: 200 });
      setMunicipalities(res.municipalities);
    } catch {
      // Fallback to offline bundle
      try {
        const res = await fetch('/offline-data/municipalities_bundle.json');
        const raw = await res.json();
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        setMunicipalities(
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          (raw as any[]).map((d) => ({
            slug: d.slug as string,
            name: d.name as string,
            shortName: (d.short_name as string) ?? '',
            city: d.city as string,
            stateCode: (d.state_code as string) ?? '',
            municipalityType: (d.municipality_type as string) ?? '',
            wardCount: d.ward_count as number | null ?? null,
            population: d.population as number | null ?? null,
            helplinePhone: (d.helpline_phone as string) ?? null,
            centroidLat: (d.centroid_lat as number) ?? 0,
            centroidLon: (d.centroid_lon as number) ?? 0,
          }))
        );
      } catch {
        setMunicipalities([]);
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Find nearby municipalities using GPS
  const findNearby = useCallback(async () => {
    /* istanbul ignore if */if (!navigator.geolocation) return;
    setLocating(true);
    /* istanbul ignore next */navigator.geolocation.getCurrentPosition(
      async (pos) => {
        try {
          const nearby = await fetchNearbyMunicipalities(pos.coords.latitude, pos.coords.longitude, 20);
          setMunicipalities(nearby);
          setNearbyMode(true);
          setSelectedState('');
          setSelectedType('');
          setSearchQuery('');
        } catch {
          // Fallback: sort existing by distance
          const lat = pos.coords.latitude;
          const lon = pos.coords.longitude;
          setMunicipalities((prev) =>
            [...prev]
              .map((m) => ({
                ...m,
                distanceKm: Math.sqrt(Math.pow((m.centroidLat - lat) * 111, 2) + Math.pow((m.centroidLon - lon) * 111 * Math.cos(lat * Math.PI / 180), 2)),
              }))
              .sort((a, b) => (a.distanceKm ?? 999) - (b.distanceKm ?? 999))
          );
          setNearbyMode(true);
        }
        setLocating(false);
      },
      () => setLocating(false),
      { enableHighAccuracy: true, timeout: 10000 }
    );
  }, []);

  // Filter municipalities
  const filtered = useMemo(() => {
    let result = municipalities;
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      result = result.filter(
        (m) =>
          m.name.toLowerCase().includes(q) ||
          m.city.toLowerCase().includes(q) ||
          m.shortName.toLowerCase().includes(q) ||
          m.stateCode.toLowerCase().includes(q)
      );
    }
    if (selectedState) {
      result = result.filter((m) => m.stateCode === selectedState);
    }
    if (selectedType) {
      result = result.filter((m) => m.municipalityType === selectedType);
    }
    return result;
  }, [municipalities, searchQuery, selectedState, selectedType]);

  return (
    <div className="min-h-screen bg-surface-1 px-4 md:px-8 py-6 pb-24">
      <h1 className="sr-only">Municipality Guide</h1>
      {/* Header */}
      <TerminalHeader
        title={t('guide.title', 'Municipality Guide')}
        subtitle={t('guide.subtitle', '{{count}} municipalities across India', { count: municipalities.length })}
      />

      {/* Search + Actions */}
      <div className="mt-6 flex flex-col sm:flex-row gap-3">
        {/* Search */}
        <div className="relative flex-1">
          <Search size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-text-3" />
          <input
            id="guide-search"
            type="text"
            placeholder={t('guide.search_placeholder', 'Search municipality...')}
            aria-label={t('guide.search_aria_label', 'Search municipalities')}
            value={searchQuery}
            onChange={(e) => { setSearchQuery(e.target.value); setNearbyMode(false); }}
            className="w-full pl-10 pr-4 py-3 bg-surface-2 border border-border rounded-xl text-sm text-text-1 placeholder:text-text-3 focus:outline-none focus:border-brand/50 transition-colors"
          />
        </div>

        {/* Find Nearby */}
        <button
          id="guide-find-nearby"
          onClick={findNearby}
          disabled={locating}
          className="flex items-center justify-center gap-2 px-5 py-3 bg-brand/20 border border-brand/30 rounded-xl text-sm font-semibold text-brand-light hover:bg-brand/30 transition-colors disabled:opacity-50 shrink-0"
        >
          {locating ? <Loader2 size={16} className="animate-spin" /> : <Navigation size={16} />}
          {t('guide.find_nearby', 'Find Nearby')}
        </button>

        {/* Filter toggle */}
        <button
          onClick={() => setShowFilters(!showFilters)}
          className={`flex items-center gap-2 px-4 py-3 rounded-xl text-sm font-semibold border transition-colors shrink-0 ${
            showFilters || selectedState || selectedType
              ? 'bg-brand/20 border-brand/30 text-brand-light'
              : 'bg-surface-2 border-border text-text-2 hover:text-text-1'
          }`}
        >
          <Filter size={16} />
          {t('guide.filter', 'Filter')}
        </button>
      </div>

      {/* Filter chips */}
      {showFilters && (
        <div className="mt-4 p-4 rounded-xl bg-surface-2/50 border border-border space-y-4">
          {/* State filters */}
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-widest text-text-3 mb-2">{t('guide.state', 'State')}</p>
            <div className="flex flex-wrap gap-2">
              <button
                onClick={() => setSelectedState('')}
                className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-colors ${
                  !selectedState ? 'bg-brand text-white' : 'bg-surface-3 text-text-2 hover:text-text-1'
                }`}
              >
                {t('guide.all', 'All')}
              </button>
              {STATE_CHIPS.map((s) => (
                <button
                  key={s}
                  onClick={() => setSelectedState(selectedState === s ? '' : s)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-colors ${
                    selectedState === s ? 'bg-brand text-white' : 'bg-surface-3 text-text-2 hover:text-text-1'
                  }`}
                >
                  {s}
                </button>
              ))}
            </div>
          </div>

          {/* Type filters */}
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-widest text-text-3 mb-2">{t('guide.type', 'Type')}</p>
            <div className="flex flex-wrap gap-2">
              {TYPE_FILTERS.map((tItem) => (
                <button
                  key={tItem.value}
                  onClick={() => setSelectedType(selectedType === tItem.value ? '' : tItem.value)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-colors ${
                    selectedType === tItem.value ? 'bg-brand text-white' : 'bg-surface-3 text-text-2 hover:text-text-1'
                  }`}
                >
                  {t(tItem.labelKey, tItem.defaultLabel)}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Nearby mode indicator */}
      {nearbyMode && (
        <div className="mt-4 flex items-center gap-2 text-brand-light text-sm">
          <MapPin size={14} />
          <span className="font-semibold">{t('guide.sorted_by_distance', 'Sorted by distance from your location')}</span>
          <button
            onClick={() => { setNearbyMode(false); loadData(); }}
            className="ml-auto text-xs text-text-3 hover:text-text-1 underline"
          >
            {t('guide.reset', 'Reset')}
          </button>
        </div>
      )}

      {/* Results count */}
      <div className="mt-4 flex items-center justify-between">
        <p className="text-xs text-text-3 font-mono">
          {t('guide.results_count', '{{filteredCount}} of {{totalCount}} municipalities', { filteredCount: filtered.length, totalCount: municipalities.length })}
        </p>
        {(searchQuery || selectedState || selectedType) && (
          <button
            onClick={() => { setSearchQuery(''); setSelectedState(''); setSelectedType(''); }}
            className="text-xs text-brand-light hover:underline"
          >
            {t('guide.clear_filters', 'Clear filters')}
          </button>
        )}
      </div>

      {/* Loading */}
      {loading && (
        <div className="mt-16 flex flex-col items-center gap-4">
          <Loader2 size={32} className="animate-spin text-brand" />
          <p className="text-sm font-semibold uppercase tracking-widest text-text-3">{t('guide.loading_municipalities', 'Loading municipalities...')}</p>
        </div>
      )}

      {/* Grid */}
      {!loading && (
        <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {filtered.map((m) => (
            <MunicipalityCard key={m.slug} municipality={m} />
          ))}
        </div>
      )}

      {/* Empty state */}
      {!loading && filtered.length === 0 && (
        <div className="mt-16 flex flex-col items-center gap-4">
          <Building2 size={48} className="text-text-3" />
          <p className="text-sm font-semibold text-text-3">{t('guide.no_municipalities_found', 'No municipalities found')}</p>
          <p className="text-xs text-text-3">{t('guide.try_different_search', 'Try a different search term or filter')}</p>
        </div>
      )}

      {/* How to Use section */}
      {!loading && !searchQuery && !selectedState && !selectedType && !nearbyMode && (
        <div className="mt-12 p-6 rounded-2xl bg-surface-2/40 border border-border">
          <h2 className="text-lg font-bold text-text-1 mb-3">{t('guide.how_to_use', 'How to Use This Guide')}</h2>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-sm text-text-2">
            <div className="flex items-start gap-3">
              <div className="p-2 rounded-lg bg-brand/10 text-brand-light shrink-0">
                <Search size={18} />
              </div>
              <div>
                <p className="font-semibold text-text-1 mb-1">{t('guide.how_to_use_search_title', 'Search')}</p>
                <p>{t('guide.how_to_use_search_desc', 'Find any municipality by name, city, or state code')}</p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <div className="p-2 rounded-lg bg-brand/10 text-brand-light shrink-0">
                <Navigation size={18} />
              </div>
              <div>
                <p className="font-semibold text-text-1 mb-1">{t('guide.how_to_use_nearby_title', 'Find Nearby')}</p>
                <p>{t('guide.how_to_use_nearby_desc', 'Use GPS to find the nearest municipal offices to you')}</p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <div className="p-2 rounded-lg bg-brand/10 text-brand-light shrink-0">
                <MapPin size={18} />
              </div>
              <div>
                <p className="font-semibold text-text-1 mb-1">{t('guide.how_to_use_details_title', 'View Details')}</p>
                <p>{t('guide.how_to_use_details_desc', 'Click any card for contact info, leadership, and services')}</p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}