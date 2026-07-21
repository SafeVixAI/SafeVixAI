'use client';

// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team


import React from 'react';
import { AlertCircle, CloudRain, Car, AlertTriangle } from 'lucide-react';

import { useShallow } from 'zustand/react/shallow';
import { useAppStore } from '@/lib/store';

function getAlertVisual(issueType: string, severity: number) {
  const normalized = issueType.toLowerCase();

  if (severity >= 4) {
    return {
      icon: <AlertCircle size={18} strokeWidth={2.5} />,
      iconClass: 'text-emergency',
      borderClass: 'border-red-500/30',
    };
  }

  if (normalized.includes('flood') || normalized.includes('rain')) {
    return {
      icon: <CloudRain size={18} strokeWidth={2.5} />,
      iconClass: 'text-brand',
      borderClass: 'border-brand/30',
    };
  }

  if (normalized.includes('traffic') || normalized.includes('accident')) {
    return {
      icon: <Car size={18} strokeWidth={2.5} />,
      iconClass: 'text-orange-500',
      borderClass: 'border-orange-500/30',
    };
  }

  return {
    icon: <AlertTriangle size={18} strokeWidth={2.5} />,
    iconClass: 'text-warning',
    borderClass: 'border-amber-500/30',
  };
}

function formatIssueType(issueType: string) {
  return issueType
    .replaceAll('_', ' ')
    .replace(/\b\w/g, (match) => match.toUpperCase());
}

export default function RecentAlertsOverlay() {
  const { isDesktopSidebarCollapsed, nearbyRoadIssues } = useAppStore(useShallow((state) => ({
    isDesktopSidebarCollapsed: state.isDesktopSidebarCollapsed,
    nearbyRoadIssues: state.nearbyRoadIssues,
  })));

  const visibleIssues = nearbyRoadIssues.slice(0, 3);
  const summaryLabel =
    nearbyRoadIssues.length > 0
      ? `${nearbyRoadIssues.length} active alerts nearby`
      : 'No active alerts nearby';

  return (
    <div
      className={`fixed bottom-24 lg:bottom-4 left-0 w-full z-40 pointer-events-none pl-4 pr-20 flex flex-col items-center lg:pr-0 transition-all duration-300 ${isDesktopSidebarCollapsed ? 'lg:pl-[88px]' : 'lg:pl-[280px]'}`}
    >
      <div className="w-fit max-w-full pointer-events-auto flex flex-col gap-2">
        <div className="self-center sv-glass rounded-full px-4 py-1.5 shadow-xl flex items-center gap-2">
          <span
            className={`w-1.5 h-1.5 rounded-full glow-breathe ${nearbyRoadIssues.length > 0 ? 'bg-emergency shadow-[0_0_8px_var(--emergency)]' : 'bg-brand-light'}`}
          />
          <span className="text-[10px] font-semibold tracking-[0.1em] text-text-1 dark:text-brand uppercase font-space">
            {summaryLabel}
          </span>
        </div>

        {visibleIssues.length > 0 ? (
          <div className="flex justify-center gap-3 overflow-x-auto pb-2 px-2 [&::-webkit-scrollbar]:hidden [-ms-overflow-style:none] [scrollbar-width:none] scroll-smooth snap-x snap-mandatory">
            {visibleIssues.map((issue) => {
              const visual = getAlertVisual(issue.issueType, issue.severity);
              return (
                <div
                  key={issue.uuid}
                  className={`snap-center flex-shrink-0 sv-hover-magnetic sv-glass rounded-full ${visual.borderClass} px-3 py-1.5 shadow-lg flex items-center justify-center gap-2 cursor-pointer transition-colors relative border`}
                >
                  <div className={visual.iconClass}>
                    {visual.icon}
                  </div>
                  <span className="text-xs font-semibold text-text-1 dark:text-text-1 truncate">
                    {formatIssueType(issue.issueType)}
                  </span>
                </div>
              );
            })}
          </div>
        ) : null}
      </div>
    </div>
  );
}