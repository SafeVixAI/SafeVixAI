'use client';

// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team


import React from 'react';
import { useAppStore } from '../lib/store';
import { ChevronRight, ChevronLeft, AlertTriangle, ShieldCheck, MapPin, Navigation, Zap, Activity, Shield, Circle } from 'lucide-react';
import { useShallow } from 'zustand/react/shallow';
import { useTranslation } from 'react-i18next';

export function RightSidebar() {
  const [isPanelOpen, setIsPanelOpen] = React.useState(false);
  const { gpsLocation, nearbyServices, nearbyRoadIssues, serviceSearchMeta, connectivity } = useAppStore(useShallow((s) => ({ gpsLocation: s.gpsLocation, nearbyServices: s.nearbyServices, nearbyRoadIssues: s.nearbyRoadIssues, serviceSearchMeta: s.serviceSearchMeta, connectivity: s.connectivity })));
  const { t } = useTranslation('common');

  const issueCount = nearbyRoadIssues.length;
  const serviceCount = nearbyServices.length;
  const openIssues = nearbyRoadIssues.filter(i => i.status === 'open').length;

  const areaStatus = openIssues === 0 ? 'secure' : openIssues <= 2 ? 'caution' : 'alert';

  React.useEffect(() => {
    const query = window.matchMedia('(min-width: 1024px)');
    const syncPanelToViewport = () => setIsPanelOpen(query.matches);

    syncPanelToViewport();
    query.addEventListener('change', syncPanelToViewport);
    return () => query.removeEventListener('change', syncPanelToViewport);
  }, []);

  const statusConfig = {
    secure: {
      label: t('common.secure_region', 'Secure Region'),
      sub: t('common.secure_desc', 'No critical anomalies in {{radius}}km radius', { radius: serviceSearchMeta.radiusUsed ? (serviceSearchMeta.radiusUsed / 1000).toFixed(1) : '5.0' }),
      icon: <ShieldCheck className="w-5 h-5 text-brand-light" />,
      bg: 'bg-brand-light/10 border-brand-light/20',
      iconBg: 'bg-brand-light/20',
      text: 'text-brand-light',
      sub_text: 'text-brand-light/80',
    },
    caution: {
      label: t('common.caution_zone', 'Caution Zone'),
      sub: t('common.caution_desc', '{{count}} active hazard nearby — proceed with care', { count: openIssues }),
      icon: <AlertTriangle className="w-5 h-5 text-text-amber" />,
      bg: 'bg-text-amber/10 border-text-amber/20',
      iconBg: 'bg-text-amber/20',
      text: 'text-text-amber',
      sub_text: 'text-text-amber/80',
    },
    alert: {
      label: t('common.high_risk_area', 'High Risk Area'),
      sub: t('common.alert_desc', '{{count}} unresolved hazards detected — SOS ready', { count: openIssues }),
      icon: <Shield className="w-5 h-5 text-emergency" />,
      bg: 'bg-emergency/10 border-emergency/20',
      iconBg: 'bg-emergency/20',
      text: 'text-emergency',
      sub_text: 'text-emergency/80',
    },
  };

  const sc = statusConfig[areaStatus];

  return (
    <aside
      className={`fixed inset-x-0 bottom-0 z-40 flex flex-col bg-surface-1/95 backdrop-blur-3xl transition-all duration-300 border-t border-border rounded-t-2xl shadow-[0_-8px_30px_rgb(0,0,0,0.12)] lg:shadow-none lg:relative lg:inset-auto lg:h-full lg:rounded-none lg:border-t-0 lg:border-l shrink-0 ${isPanelOpen ? 'translate-y-0 lg:w-[320px] xl:w-[380px]' : 'translate-y-[calc(100%-60px)] lg:translate-y-0 lg:w-0 lg:border-none'}`}
    >
      {/* Desktop Toggle Button */}
      <button
        onClick={() => setIsPanelOpen(!isPanelOpen)}
        className={`hidden lg:flex absolute top-1/2 -translate-y-1/2 w-8 h-16 bg-surface-2 border border-border rounded-l-xl items-center justify-center shadow-lg hover:bg-surface-3 transition-colors z-50 text-text-3 ${isPanelOpen ? '-left-4' : '-left-8'}`}
        aria-label={isPanelOpen ? t('common.collapse_panel', 'Collapse panel') : t('common.expand_panel', 'Expand panel')}
        aria-controls="area-intelligence-panel"
      >
        {isPanelOpen ? <ChevronRight size={20} /> : <ChevronLeft size={20} />}
      </button>

      <button
        type="button"
        className="lg:hidden w-full h-14 absolute top-0 left-0 z-50 flex flex-col items-center justify-start pt-2 cursor-pointer"
        onClick={() => setIsPanelOpen(!isPanelOpen)}
        aria-expanded={isPanelOpen}
        aria-label={isPanelOpen ? t('common.collapse_panel', 'Collapse panel') : t('common.expand_panel', 'Expand panel')}
        aria-controls="area-intelligence-panel"
      >
        <div className="w-12 h-1.5 bg-border rounded-full" />
      </button>

      <div
        id="area-intelligence-panel"
        className={`flex-1 flex flex-col overflow-hidden transition-opacity duration-300 ${isPanelOpen ? 'opacity-100' : 'opacity-100 lg:opacity-0 lg:pointer-events-none'}`}>
        <div className="flex-1 overflow-y-auto scrollbar-hide w-full lg:w-[320px] xl:w-[380px] pt-4 lg:pt-0">
          {/* Panel Header */}
          <div className="sticky top-0 bg-surface-2/90 backdrop-blur-md border-b border-border px-6 py-4 z-10 flex items-center justify-between">
            <div>
              <h2 className="text-base font-bold text-text-1 uppercase tracking-tight font-mono">
                {t('common.area_intelligence', 'Area Intelligence')}
              </h2>
              {gpsLocation && (
                <p className="text-[11px] font-semibold text-text-3 font-mono uppercase tracking-widest mt-1">
                  <MapPin size={11} className="inline mr-1" />
                  {gpsLocation.city ?? t('common.location_detected', 'Location detected')}{gpsLocation.state ? `, ${gpsLocation.state}` : ''}
                </p>
              )}
            </div>
            {/* Connectivity indicator */}
            <div className={`flex items-center gap-1.5 px-2 py-1 rounded-sm text-[11px] font-semibold uppercase tracking-widest ${
              connectivity === 'online'
                ? 'bg-brand-light/10 text-brand-light border border-brand-light/20'
                : 'bg-text-amber/10 text-text-amber border border-text-amber/20'
            }`}>
              <span className={`w-1.5 h-1.5 rounded-full ${connectivity === 'online' ? 'bg-brand-light animate-pulse' : 'bg-text-amber'}`} />
              {connectivity === 'online' ? t('common.live', 'Live') : t('common.cached', 'Cached')}
            </div>
          </div>

          <div className="p-5 space-y-4">
            {/* Status Card */}
            <div className={`${sc.bg} border rounded-lg p-4 flex items-start gap-3`}>
              <div className={`${sc.iconBg} p-2 rounded-full mt-0.5 flex-shrink-0`}>
                {sc.icon}
              </div>
              <div>
                <h3 className={`font-semibold text-sm ${sc.text}`}>{sc.label}</h3>
                <p className={`text-[13px] ${sc.sub_text} mt-1 leading-relaxed`}>{sc.sub}</p>
              </div>
            </div>

            {/* Stats Row */}
            <div className="grid grid-cols-2 gap-3">
              <div className="flex flex-col gap-1.5 p-4 rounded-lg bg-surface-2 border border-border">
                <div className="flex items-center gap-1.5">
                  <Navigation size={12} className="text-brand-light" />
                  <span className="text-[11px] font-semibold text-text-3 font-mono uppercase tracking-widest">{t('common.services', 'Services')}</span>
                </div>
                <p className="text-2xl font-black text-text-1">{serviceCount}</p>
                <p className="text-[11px] font-semibold text-text-3 font-mono uppercase tracking-wider">{t('common.nearby_found', 'Nearby Found')}</p>
              </div>
              <div className="flex flex-col gap-1.5 p-4 rounded-lg bg-surface-2 border border-border">
                <div className="flex items-center gap-1.5">
                  <AlertTriangle size={12} className="text-text-amber" />
                  <span className="text-[11px] font-semibold text-text-3 font-mono uppercase tracking-widest">{t('common.hazards', 'Hazards')}</span>
                </div>
                <p className="text-2xl font-black text-text-1">{issueCount}</p>
                <p className="text-[11px] font-semibold text-text-3 font-mono uppercase tracking-wider">
                  {t('common.open_count', '{{count}} Open', { count: openIssues })}
                </p>
              </div>
            </div>

            {/* Live Road Issues */}
            {nearbyRoadIssues.length > 0 && (
              <div className="flex flex-col gap-2">
                <p className="text-[11px] font-semibold text-text-3 uppercase tracking-[0.05em] px-1 mt-2">{t('common.active_hazards', 'Active Hazards')}</p>
                {nearbyRoadIssues.slice(0, 4).map((issue) => (
                  <div
                    key={issue.uuid}
                    className="flex items-start gap-3 p-3 rounded-xl bg-surface-2 border border-border hover:border-text-amber/30 transition-colors"
                  >
                    <div className="w-8 h-8 rounded-lg bg-text-amber/10 flex items-center justify-center flex-shrink-0 mt-0.5">
                      <AlertTriangle size={14} className="text-text-amber" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-[13px] font-bold text-text-1 font-mono uppercase tracking-tight truncate">
                        {issue.issueType.replace(/_/g, ' ')}
                      </p>
                      <p className="text-[11px] font-medium text-text-3 font-mono uppercase tracking-wider mt-0.5">
                        {issue.roadName || 'Unknown Road'} · {(issue.distance / 1000).toFixed(1)}km
                      </p>
                    </div>
                    <span className={`text-[11px] font-bold font-mono uppercase tracking-wider px-2 py-0.5 rounded flex-shrink-0 ${
                      issue.severity >= 3
                        ? 'bg-emergency/10 text-emergency'
                        : 'bg-text-amber/10 text-text-amber'
                    }`}>
                      S{issue.severity}
                    </span>
                  </div>
                ))}
              </div>
            )}

            {/* No data yet */}
            {serviceCount === 0 && issueCount === 0 && (
              <div className="flex flex-col items-center gap-3 py-8 text-center mt-4">
                <div className="w-12 h-12 rounded-lg bg-surface-2 flex items-center justify-center">
                  <Activity size={20} className="text-text-3" />
                </div>
                <p className="text-[13px] font-semibold text-text-2 uppercase tracking-widest font-mono">{t('common.scanning_area', 'Scanning Area...')}</p>
                <p className="text-[11px] font-medium text-text-3 max-w-[180px] leading-relaxed">
                  {t('common.allow_location_desc', 'Allow location to activate live hazard intelligence')}
                </p>
              </div>
            )}

            {/* Driving Score */}
            <div className="p-4 rounded-lg bg-gradient-to-br from-brand/10 to-brand-light/5 border border-brand/20 flex items-center gap-4 mt-2 mb-10 lg:mb-2">
              <div className="w-12 h-12 rounded-xl bg-brand/10 flex items-center justify-center">
                <Zap size={20} className="text-brand-light" />
              </div>
              <div className="flex-1">
                <p className="text-[11px] font-semibold text-text-3 uppercase tracking-widest font-mono">{t('common.ai_sentinel', 'AI Sentinel')}</p>
                <p className="text-[13px] font-bold text-text-1 uppercase tracking-tight font-mono">{t('common.monitoring_active', 'Monitoring Active')}</p>
              </div>
              <div className="flex items-center gap-1">
                <Circle size={8} className="fill-brand-light text-brand-light animate-pulse" />
              </div>
            </div>
          </div>
        </div>
      </div>
    </aside>
  );
}