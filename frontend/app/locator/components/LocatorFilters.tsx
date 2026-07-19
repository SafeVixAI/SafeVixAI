// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
import React from 'react';

import { FILTER_CHIPS, Filter } from '../locator-utils';

export function LocatorFilters({
  activeFilter,
  setActiveFilter,
  className = '',
}: {
  activeFilter: Filter;
  setActiveFilter: (  _filter: Filter) => void;
  className?: string;
}) {
  return (
    <div
      role="radiogroup"
      aria-label="Filter facilities by type"
      className={`flex overflow-x-auto gap-3 pb-4 scroll-smooth [scrollbar-width:none] [&::-webkit-scrollbar]:hidden ${className}`}
    >
      {FILTER_CHIPS.map((chip) => (
        <button
          key={chip}
          role="radio"
          aria-checked={activeFilter === chip}
          onClick={() => setActiveFilter(chip)}
          aria-label={`Filter by ${chip}`}
          className={`flex-none px-5 py-2.5 rounded-xl font-black text-[10px] uppercase tracking-widest transition-all active:scale-95 flex items-center gap-2 ${
            activeFilter === chip
              ? 'bg-brand text-white shadow-lg shadow-brand/30 ring-1 ring-white/20'
              : 'bg-white dark:bg-surface-2/60 backdrop-blur-md border border-border-md dark:border-white/10 text-text-2 dark:text-text-2 shadow-sm'
          }`}
        >
          {chip}
        </button>
      ))}
    </div>
  );
}
