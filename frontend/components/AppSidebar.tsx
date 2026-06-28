// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  MapPin,
  BotMessageSquare,
  MapPinPlus,
  HeartPulse,
  AlertTriangle,
  Scale,
  ShieldAlert,
  User,
  Settings,
  Phone,
  Menu,
  X,
  PanelLeft,
  Building2,
  Cpu
} from 'lucide-react';
import { useAppStore } from '@/lib/store';
import { Logo } from '@/components/ui/Logo';

const navItems = [
  { icon: <MapPin size={20} />, label: 'Map', href: '/', color: 'text-brand-light' },
  { icon: <BotMessageSquare size={20} />, label: 'AI Assistant', href: '/assistant', color: 'text-brand-light' },
  { icon: <MapPinPlus size={20} />, label: 'Locator', href: '/locator', color: 'text-brand-light' },
  { icon: <HeartPulse size={20} />, label: 'First Aid', href: '/first-aid', color: 'text-emergency' },
  { icon: <AlertTriangle size={20} />, label: 'Report Road Issue', href: '/report', color: 'text-warning' },
  { icon: <Scale size={20} />, label: 'Challan Calculator', href: '/challan', color: 'text-text-3' },
  { icon: <ShieldAlert size={20} />, label: 'Emergency', href: '/emergency', color: 'text-emergency' },
  { icon: <Building2 size={20} />, label: 'Municipality Guide', href: '/guide', color: 'text-brand-light' },
  { icon: <Cpu size={20} />, label: 'Providers', href: '/providers', color: 'text-brand-light' },
  { icon: <User size={20} />, label: 'Profile', href: '/profile', color: 'text-brand-light' },
  { icon: <Settings size={20} />, label: 'Settings', href: '/settings', color: 'text-text-3' },
];

const quickDials = [
  { label: 'Emergency', number: '112', icon: <Phone size={16} /> },
  { label: 'Ambulance', number: '102', icon: <HeartPulse size={16} /> },
  { label: 'Police', number: '100', icon: <ShieldAlert size={16} /> },
  { label: 'Highway', number: '1033', icon: <MapPinPlus size={16} /> },
];

export function AppSidebar() {
  const pathname = usePathname();
  const isDesktopSidebarCollapsed = useAppStore((state) => state.isDesktopSidebarCollapsed);
  const setDesktopSidebarCollapsed = useAppStore((state) => state.setDesktopSidebarCollapsed);
  const isThinSidebarEnabled = useAppStore((state) => state.isThinSidebarEnabled);
  const setThinSidebarEnabled = useAppStore((state) => state.setThinSidebarEnabled);

  return (
    <aside
      className={`fixed left-0 top-0 h-full z-50 bg-surface-1/95 backdrop-blur-3xl flex flex-col border-r border-border transition-all duration-300 ${
        isDesktopSidebarCollapsed && !isThinSidebarEnabled
          ? 'opacity-0 pointer-events-none shadow-none'
          : 'opacity-100 pointer-events-auto shadow-panel'
      } ${!isDesktopSidebarCollapsed ? 'w-[280px]' : isThinSidebarEnabled ? 'w-[88px]' : 'w-[280px]'}`}
    >

      {/* Header (Logo and Toggle) or Hamburger */}
      {!isDesktopSidebarCollapsed ? (
        <div className="flex flex-col border-b border-border bg-surface-2/50 backdrop-blur-xl shrink-0">
          <div className="flex items-center justify-between p-6 pb-2">
            <div className="flex items-center gap-3">
              <Logo size={38} status="online" />
              <div className="whitespace-nowrap">
                <h2 className="text-xl font-black text-text-1 tracking-tight leading-none font-mono">SAFEVIX_AI</h2>
                <p className="text-[10px] font-bold text-brand-light uppercase tracking-widest mt-1">System Integrated</p>
              </div>
            </div>
              <button
              onClick={() => setDesktopSidebarCollapsed(true)}
              aria-label="Close sidebar"
              className="p-1.5 rounded-lg text-text-3 hover:text-text-1 hover:bg-surface-3 transition-colors"
            >
              <X size={20} />
            </button>
          </div>
          
          {/* Toggle Sidebar Button (Google Maps Style) */}
          <div className="px-2 pb-3">
            <button
              onClick={() => setThinSidebarEnabled(!isThinSidebarEnabled)}
              aria-label={isThinSidebarEnabled ? "Unpin sidebar" : "Pin sidebar"}
              className="flex items-center w-full transition-colors hover:bg-surface-3 py-3 px-4 rounded-xl justify-between group"
            >
              <div className="flex items-center gap-4">
                <PanelLeft className="w-[20px] h-[20px] text-text-3 group-hover:text-text-1 transition-colors" strokeWidth={1.5} />
                <span className="text-[14px] font-normal text-text-2 group-hover:text-text-1 whitespace-nowrap transition-colors">Show side bar</span>
              </div>
              {/* Material Design Toggle Switch */}
              <div className={`relative flex items-center shrink-0 w-8 h-3.5 rounded-full transition-colors ${isThinSidebarEnabled ? 'bg-brand/50' : 'bg-surface-3'}`}>
                <span className={`absolute w-5 h-5 rounded-full transition-transform shadow-md ${isThinSidebarEnabled ? 'bg-brand-light translate-x-4' : 'bg-text-2 -translate-x-1'}`} />
              </div>
            </button>
          </div>
        </div>
      ) : (
        <div className="flex justify-center p-4 border-b border-border bg-surface-2/50 backdrop-blur-xl shrink-0">
          <button
            onClick={() => setDesktopSidebarCollapsed(false)}
            aria-label="Expand sidebar"
            className="w-12 h-12 flex items-center justify-center rounded-xl text-text-3 hover:text-text-1 hover:bg-surface-3 transition-colors hover:scale-105 active:scale-95"
          >
            <Menu size={24} strokeWidth={2} />
          </button>
        </div>
      )}

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto py-2 space-y-4 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">

        <div className="px-3">
          <div className="flex flex-col gap-1 relative">
            {navItems.map((item) => {
              const isActive = pathname === item.href;
              
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  title={isDesktopSidebarCollapsed ? item.label : undefined}
                  className={`relative flex items-center gap-3 px-3 py-3 rounded-xl transition-all group z-10 ${isActive
                    ? ''
                    : 'hover:bg-surface-2 font-medium'
                    } ${isDesktopSidebarCollapsed ? 'justify-center' : ''}`}
                >
                  {isActive && (
                    <div
                      
                      className="absolute inset-0 bg-brand/10 rounded-xl shadow-[0_2px_10px_rgba(0,0,0,0.05)] border border-brand/20 -z-10"
                    />
                  )}
                  <div className={`${item.color} ${isActive ? 'scale-110' : 'group-hover:scale-110'} p-1.5 rounded-lg bg-current/10 transition-transform shrink-0`}>
                    {item.icon}
                  </div>
                  {!isDesktopSidebarCollapsed && (
                    <span className={`text-[14px] whitespace-nowrap transition-colors font-mono tracking-tight uppercase ${isActive
                      ? 'font-bold text-text-1'
                      : 'text-text-2 group-hover:text-text-1'
                      }`}>
                      {item.label}
                    </span>
                  )}
                </Link>
              );
            })}
          </div>
        </div>

        {/* Quick Dial Section */}
        {!isDesktopSidebarCollapsed && (
          <div>
            <div className="flex items-center justify-between px-2 mb-3 mt-4">
              <p className="text-[10px] font-semibold tracking-[0.1em] text-emergency uppercase whitespace-nowrap">Emergency Dial</p>
              <div className="h-px flex-1 bg-emergency-dim ml-3"></div>
            </div>
            <div className="grid grid-cols-2 gap-2">
              {quickDials.map((dial) => (
                <a
                  key={dial.label}
                  href={`tel:${dial.number}`}
                  className="relative flex flex-col items-center justify-center p-3 rounded-xl bg-surface-2 hover:bg-surface-3 border border-border transition-all group overflow-hidden"
                >
                  <div className="absolute inset-0 bg-gradient-to-br from-emergency/[0.05] to-transparent pointer-events-none" />
                  <div className="text-emergency mb-1 group-hover:scale-110 transition-[transform,color]">
                    {dial.icon}
                  </div>
                  <p className="text-[9px] font-semibold text-text-3 font-mono uppercase tracking-widest whitespace-nowrap mb-0.5">{dial.label}</p>
                  <p className="text-xs font-bold text-text-1 font-mono leading-none whitespace-nowrap group-hover:text-emergency transition-colors">{dial.number}</p>
                </a>
              ))}
            </div>
          </div>
        )}
      </nav>

      {/* Primary Action Footer: SOS */}
      <div className={`p-4 bg-gradient-to-b from-transparent to-surface-2 border-t border-border shrink-0 flex flex-col items-center`}>
        <Link href="/sos" className="w-full">
          <button aria-label="System SOS" className={`w-full flex items-center justify-center gap-2 py-3 bg-emergency hover:bg-emergency-dark text-white rounded-xl font-black shadow-[0_4px_20px_rgba(220,38,38,0.4)] border border-red-400/50 hover:shadow-[0_4px_25px_rgba(220,38,38,0.6)] transition-all active:scale-[0.98] group overflow-hidden relative ${isDesktopSidebarCollapsed ? 'px-0' : ''}`}>
            <div
              className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent -rotate-45 translate-x-[-100%] group-hover:animate-shimmer"
            />
            <ShieldAlert className="w-7 h-7 relative z-10 shrink-0 drop-shadow-md text-white" strokeWidth={2.5} />
            {!isDesktopSidebarCollapsed && (
              <span className="relative z-10 tracking-[0.1em] font-black uppercase text-[13px] whitespace-nowrap drop-shadow-sm font-mono">System SOS</span>
            )}
          </button>
        </Link>
        {!isDesktopSidebarCollapsed && (
          <div className="flex items-center justify-center gap-2 mt-3 text-[10px] font-bold text-text-3 font-mono whitespace-nowrap">
            <div className="w-1.5 h-1.5 rounded-full bg-brand-light animate-pulse" />
            SYSTEM ONLINE
          </div>
        )}
      </div>
    </aside>
  );
}
