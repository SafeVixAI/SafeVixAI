'use client';

// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team


import React, { memo, useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { ArrowLeft, Search, Mic, Sun, Moon, Monitor, Menu, ShieldCheck, User } from 'lucide-react';
import { useAppStore } from '@/lib/store';
import { useTheme } from '@/components/ThemeProvider';
import { useTranslation } from 'react-i18next';
import { Logo } from '@/components/ui/Logo';

type ThemeChoice = 'light' | 'dark' | 'system';

interface SystemHeaderProps {
  title?: string;
  showBack?: boolean;
  backHref?: string;
  isOnlineInitial?: boolean;
}

const SystemHeader = memo(function SystemHeader({
  title = 'SafeVixAI',
  showBack = true,
  backHref = '/',
  isOnlineInitial = true
}: SystemHeaderProps) {
  const [mounted, setMounted] = useState(false);
  const [isOnline, setIsOnline] = useState(isOnlineInitial);
  const router = useRouter();
  const { theme, setTheme } = useTheme();
  const setSystemSidebarOpen = useAppStore((state) => state.setSystemSidebarOpen);
  const isAuthenticated = useAppStore((s) => s.isAuthenticated);
  const operatorName = useAppStore((s) => s.operatorName);
  const { t } = useTranslation('common');

  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    setMounted(true);
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);
    
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    setIsOnline(navigator.onLine);
    
    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    const query = searchQuery.trim();
    if (!query) return;
    router.push(`/assistant?q=${encodeURIComponent(query)}`);
  };

  return (
    <header className="hidden lg:flex fixed top-0 left-0 w-full z-50 bg-surface-1/80 backdrop-blur-2xl border-b border-border shadow-sm px-6 h-[52px] items-center justify-between transition-colors duration-500">
      <div className="flex items-center gap-4 flex-1">
        {showBack && (
          <Link 
            href={backHref} 
            aria-label={t('common.go_back', 'Go back')}
            className="text-text-2 hover:bg-surface-2 transition-colors active:scale-95 duration-200 p-2 rounded-full flex items-center justify-center border border-transparent hover:border-border"
          >
            <ArrowLeft size={20} />
          </Link>
        )}
        
        <div className="flex items-center gap-3">
          <Logo size={34} status={isOnline ? 'online' : 'offline'} />
          <div className="flex flex-col">
            <h1 
              className="text-text-1 font-black tracking-tight text-base leading-tight font-mono uppercase"
              aria-current="page"
            >
              {title}
            </h1>
            <div className="flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-brand-light/10 border border-brand-light/20 w-fit mt-0.5">
              <span className="w-1.5 h-1.5 rounded-full bg-brand-light animate-pulse"></span>
              <span className="text-[9px] font-bold text-brand-light uppercase tracking-widest font-mono">{t('common.sentinel_active', 'Sentinel Active')}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Desktop Search Bar (Google Maps Style) */}
      <form 
        onSubmit={handleSearch}
        role="search"
        aria-label="Search"
        className="flex-1 max-w-md mx-8 flex h-9 bg-surface-2 rounded-full border border-border items-center px-2 overflow-hidden transition-all duration-300 focus-within:shadow-[0_0_20px_rgba(0,200,150,0.12)] focus-within:bg-surface-3 focus-within:border-brand-light/40"
      >
        <button
          type="button"
          onClick={() => setSystemSidebarOpen(true)}
          className="p-1.5 rounded-full hover:bg-surface-3 text-text-2 transition-colors mr-1"
          title="Global Navigation"
          aria-label="Open navigation menu"
        >
          <Menu size={16} />
        </button>

        <Search className="w-4 h-4 text-text-3 shrink-0 ml-1" />
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder={t('common.search_placeholder', 'Ask Maps or Search System')}
          aria-label="Search input"
          className="flex-1 bg-transparent border-none outline-none focus:outline-none focus:ring-0 focus-visible:ring-0 px-3 text-sm text-text-1 placeholder:text-text-3 font-medium h-full w-full"
        />
        <button 
          type="button"
          aria-label="Start voice search"
          className="p-1.5 mr-1 rounded-full bg-brand/10 text-brand-light hover:bg-brand/20 transition-all"
        >
          <Mic className="w-4 h-4" />
        </button>
      </form>

      <div className="flex items-center gap-4 min-w-[280px] justify-end">
        {/* Connection Status */}
        <div className="flex bg-surface-2 rounded-xl p-0.5 border border-border shadow-inner">
          <button
            title="Force Online Mode"
            disabled={isOnline}
            className={`px-3 py-1 text-[11px] rounded-lg font-bold transition-all duration-200 ${isOnline ? 'bg-surface-3 text-text-1 shadow-sm ring-1 ring-border' : 'text-text-3 hover:text-text-1'}`}
          >
            {t('common.online', 'Online')}
          </button>
          <button
            title="Force Offline Mode"
            disabled={!isOnline}
            className={`px-3 py-1 text-[11px] rounded-lg font-bold transition-all duration-200 ${!isOnline ? 'bg-surface-3 text-text-1 shadow-sm ring-1 ring-border' : 'text-text-3 hover:text-text-1'}`}
          >
            {t('common.offline', 'Offline')}
          </button>
        </div>

        {/* Theme Switcher */}
        {mounted && (
          <div className="flex items-center h-8 gap-1 bg-surface-2 rounded-full p-1 border border-border shadow-sm">
            {([
              { id: 'light', icon: <Sun size={14} />, label: t('common.light_mode', 'Light mode') },
              { id: 'dark', icon: <Moon size={14} />, label: t('common.dark_mode', 'Dark mode') },
              { id: 'system', icon: <Monitor size={14} />, label: t('common.auto_theme', 'Auto theme') }
            ] satisfies Array<{ id: ThemeChoice; icon: React.ReactNode; label: string }>).map((tObj) => (
              <button
                key={tObj.id}
                onClick={() => setTheme(tObj.id)}
                aria-label={tObj.label}
                className={`p-1 rounded-full transition-all ${theme === tObj.id ? 'bg-brand/20 text-brand-light shadow-sm' : 'text-text-3 hover:text-text-1'}`}
              >
                {tObj.icon}
              </button>
            ))}
          </div>
        )}

        {/* Operator Chip (only when authenticated) */}
        {isAuthenticated && operatorName && (
          <div className="hidden xl:flex items-center gap-2 bg-brand/20 px-3 py-1.5 rounded-full border border-brand/30">
            <User size={12} className="text-brand-light" />
            <span className="text-[10px] uppercase tracking-widest font-black text-brand-light max-w-[120px] truncate">{operatorName}</span>
          </div>
        )}

        <div className="hidden xl:flex items-center gap-2 bg-brand-light/10 px-3 py-1.5 rounded-full border border-brand-light/20 shadow-sm">
          <ShieldCheck size={14} className="text-brand-light" />
          <span className="text-[10px] uppercase tracking-widest font-black text-brand-light">{t('common.secure', 'Secure')}</span>
        </div>
      </div>
    </header>
  );
});

export default SystemHeader;