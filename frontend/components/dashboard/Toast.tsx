'use client';

// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team


import React, { useEffect } from 'react';
import { CheckCircle, AlertCircle, Info, X } from 'lucide-react';

type ToastType = 'success' | 'error' | 'info';

interface ToastProps {
  message: string;
  type?: ToastType;
  isVisible: boolean;
  onClose: () => void;
  duration?: number;
}

export default function Toast({ message, type = 'info', isVisible, onClose, duration = 3000 }: ToastProps) {
  useEffect(() => {
    if (isVisible && duration > 0) {
      const timer = setTimeout(() => {
        onClose();
      }, duration);
      return () => clearTimeout(timer);
    }
  }, [isVisible, duration, onClose]);

  const Icon = type === 'success' ? CheckCircle : type === 'error' ? AlertCircle : Info;
  const getColors = (t: ToastType): string => {
    switch (t) {
      case 'success':
        return 'bg-brand-light/10 border-brand-light/20 dark:bg-brand-light/10 dark:border-brand-light/20 text-brand-dim dark:text-brand-light';
      case 'error':
        return 'bg-emergency/10 border-emergency/20 dark:bg-red-500/10 dark:border-red-500/20 text-red-600 dark:text-red-400';
      case 'info':
      default:
        return 'bg-brand/8 border-brand-light/30 dark:bg-brand/10 dark:border-brand/20 text-brand dark:text-brand-light';
    }
  };

  if (!isVisible) return null;

  return (
    <div
      className="fixed bottom-24 lg:bottom-10 left-1/2 -translate-x-1/2 z-[200]"
      style={{ animation: 'fadeInUp 0.2s ease-out' }}
    >
      <div className={`flex items-center gap-3 px-5 py-3 rounded-lg border shadow-lg backdrop-blur-md ${getColors(type)}`}>
        <Icon size={18} />
        <span className="text-[11px] font-semibold uppercase tracking-widest leading-none mt-0.5">{message}</span>
        <button onClick={onClose} aria-label="Close notification" className="ml-2 hover:bg-black/5 dark:hover:bg-white/10 p-1 rounded-full transition-colors">
          <X size={14} />
        </button>
      </div>
    </div>
  );
}