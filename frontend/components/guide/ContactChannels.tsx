'use client';

// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team


import React from 'react';
import {
  Phone,
  Mail,
  Globe,
  MapPin,
  MessageCircle,
  FileText,
  Smartphone,
  ExternalLink,
} from 'lucide-react';
import type { MunicipalityDetail } from '@/lib/api';

interface ContactChannelsProps {
  municipality: MunicipalityDetail;
}

interface ChannelItem {
  label: string;
  value: string | null;
  icon: React.ReactNode;
  href?: string | null;
  isPhone?: boolean;
}

export function ContactChannels({ municipality: m }: ContactChannelsProps) {
  const channels: ChannelItem[] = [
    {
      label: 'Headquarters',
      value: m.headquartersAddress,
      icon: <MapPin size={18} />,
    },
    {
      label: 'Helpline',
      value: m.helplinePhone,
      icon: <Phone size={18} />,
      href: m.helplinePhone ? `tel:${m.helplinePhone}` : null,
      isPhone: true,
    },
    {
      label: 'Email',
      value: m.email,
      icon: <Mail size={18} />,
      href: m.email ? `mailto:${m.email}` : null,
    },
    {
      label: 'Website',
      value: m.websiteUrl ? new URL(m.websiteUrl).hostname : null,
      icon: <Globe size={18} />,
      href: m.websiteUrl,
    },
    {
      label: 'WhatsApp',
      value: m.whatsappNumber,
      icon: <MessageCircle size={18} />,
      href: m.whatsappNumber ? `https://wa.me/${m.whatsappNumber.replace(/[^0-9]/g, '')}` : null,
    },
    {
      label: 'Grievance Portal',
      value: m.grievancePortalUrl ? 'File a Complaint' : null,
      icon: <FileText size={18} />,
      href: m.grievancePortalUrl,
    },
    {
      label: 'Mobile App',
      value: m.appName,
      icon: <Smartphone size={18} />,
      href: m.appUrl,
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
      {channels.map((ch) => {
        const available = !!ch.value;
        const innerContent = (
          <>
            <div className={`p-2 rounded-lg shrink-0 ${available ? 'bg-brand/10 text-brand-light' : 'bg-surface-3 text-text-3'}`}>
              {ch.icon}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-[10px] font-semibold uppercase tracking-widest text-text-3 mb-1">{ch.label}</p>
              <p className={`text-sm font-medium truncate ${available ? 'text-text-1' : 'text-text-3'}`}>
                {ch.value ?? 'Not available'}
              </p>
            </div>
            {ch.href && available && (
              <ExternalLink size={14} className="text-text-3 group-hover:text-brand-light transition-colors mt-2 shrink-0" />
            )}
          </>
        );

        const baseClassName = `flex items-start gap-3 p-4 rounded-xl border transition-all ${
          available
            ? 'bg-surface-2/70 border-border hover:border-brand/40 hover:bg-surface-2 cursor-pointer group'
            : 'bg-surface-2/30 border-border/50 opacity-50 cursor-default'
        }`;

        if (ch.href && available) {
          return (
            <a
              key={ch.label}
              href={ch.href}
              target={ch.href.startsWith('http') ? '_blank' : undefined}
              rel="noopener noreferrer"
              className={baseClassName}
            >
              {innerContent}
            </a>
          );
        }

        return (
          <div key={ch.label} className={baseClassName}>
            {innerContent}
          </div>
        );
      })}
    </div>
  );
}