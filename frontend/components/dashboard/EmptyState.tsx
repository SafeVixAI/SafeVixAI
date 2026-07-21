'use client';

// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team


import React, { memo } from 'react';
import { SearchX, type LucideIcon } from 'lucide-react';

const EmptyState = memo(function EmptyState({ 
  title, 
  description, 
  icon: Icon = SearchX 
}: { 
  title: string; 
  description: string; 
  icon?: LucideIcon;
}) {
  return (
    <div className="w-full py-12 flex flex-col items-center justify-center text-center">
      <div className="w-16 h-16 rounded-full bg-surface-2 dark:bg-surface-3 flex items-center justify-center mb-4">
        <Icon size={24} className="text-text-2 dark:text-text-2" />
      </div>
      <h3 className="text-sm font-bold text-text-1 dark:text-white uppercase tracking-wider">{title}</h3>
      <p className="text-xs text-text-2 dark:text-text-2 mt-2 max-w-[250px] leading-relaxed">{description}</p>
    </div>
  );
});

export default EmptyState;