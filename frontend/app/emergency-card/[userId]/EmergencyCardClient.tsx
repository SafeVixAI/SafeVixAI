'use client';

// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
import React from 'react';

import { useEffect, useMemo, useState } from 'react';
import { AlertTriangle, Car, CheckCircle2, FileText, Heart, Phone, Pill, Shield } from 'lucide-react';
import { PrintButton } from './PrintButton';

export interface EmergencyCardData {
  name?: string;
  blood?: string;
  vehicle?: string;
  contact?: string;
  allergies?: string;
  insurance?: string;
  medical?: string;
}

interface EmergencyCardClientProps {
  userId: string;
  initialData: EmergencyCardData;
}

export function decodeBase64Url(value: string): string {
  const base64 = value.replace(/-/g, '+').replace(/_/g, '/');
  const padded = base64.padEnd(Math.ceil(base64.length / 4) * 4, '=');
  const binary = atob(padded);
  const bytes = Uint8Array.from(binary, (char) => char.charCodeAt(0));
  return new TextDecoder().decode(bytes);
}

export function parseHashPayload(): EmergencyCardData | null {
  const params = new URLSearchParams(window.location.hash.replace(/^#/, ''));
  const encoded = params.get('data');
  if (!encoded) return null;

  try {
    const parsed = JSON.parse(decodeBase64Url(encoded)) as EmergencyCardData;
    return {
      name: typeof parsed.name === 'string' ? parsed.name : '',
      blood: typeof parsed.blood === 'string' ? parsed.blood : '',
      vehicle: typeof parsed.vehicle === 'string' ? parsed.vehicle : '',
      contact: typeof parsed.contact === 'string' ? parsed.contact : '',
      allergies: typeof parsed.allergies === 'string' ? parsed.allergies : '',
      insurance: typeof parsed.insurance === 'string' ? parsed.insurance : '',
      medical: typeof parsed.medical === 'string' ? parsed.medical : '',
    };
  } catch {
    return null;
  }
}

export function dialablePhone(value: string): string {
  return value.replace(/[^\d+]/g, '');
}

export function EmergencyCardClient({ userId, initialData }: EmergencyCardClientProps) {
  const [data, setData] = useState<EmergencyCardData>(initialData);

  useEffect(() => {
    const payload = parseHashPayload();
    if (payload) {
      setData((current) => ({ ...current, ...payload }));
    }
  }, []);

  const hasData = !!(data.name || data.blood || data.contact);
  const emergencyContactHref = useMemo(() => {
    const phone = data.contact ? dialablePhone(data.contact) : '';
    return phone ? `tel:${phone}` : '';
  }, [data.contact]);

  return (
    <div className="min-h-screen bg-bg flex items-center justify-center p-4 font-sans">
      <h1 className="sr-only">Emergency Card</h1>
      <style>{`
        @media print {
          body { background: white !important; }
          .no-print { display: none !important; }
          .print-card { background: white !important; color: black !important; border: 2px solid #333 !important; }
          .print-card * { color: black !important; }
        }
      `}</style>

      <div className="fixed top-0 left-0 right-0 h-0.5 bg-gradient-to-r from-transparent via-brand-light to-transparent opacity-60 animate-pulse no-print" />

      <div className="relative w-full max-w-sm mx-auto">
        <div className="flex gap-2 justify-end mb-4 no-print">
          <PrintButton />
        </div>

        <div className="mb-6 text-center">
          <div className="flex items-center justify-center gap-2 mb-3">
            <div className="w-10 h-10 rounded-lg bg-brand flex items-center justify-center shadow-lg shadow-brand/40">
              <Shield size={20} className="text-white" />
            </div>
            <div className="text-left">
              <p className="text-[10px] font-black text-brand-light uppercase tracking-[0.25em]">SafeVixAI</p>
              <p className="text-[8px] font-bold text-text-2 uppercase tracking-widest">Emergency Protocol</p>
            </div>
          </div>
          <div className="flex items-center justify-center gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-brand-light animate-pulse" />
            <span className="text-[9px] font-black text-brand-light uppercase tracking-[0.1em]">
              {hasData ? 'First Responder Card Active' : 'Limited Emergency Card'}
            </span>
          </div>
        </div>

        <div className="print-card rounded-xl border border-white/10 bg-surface-1 overflow-hidden shadow-2xl shadow-black/60">
          <div className="h-1.5 bg-gradient-to-r from-brand via-brand-light to-brand" />

          <div className="bg-red-500/10 border-b border-red-500/20 px-6 py-3 flex items-center gap-3">
            <AlertTriangle size={16} className="text-red-400 flex-shrink-0 animate-pulse" />
            <p className="text-[11px] font-semibold text-red-400 uppercase tracking-widest">
              Emergency Medical Information
            </p>
          </div>

          <div className="px-6 pt-6 pb-4">
            <p className="text-[9px] font-bold text-text-2 uppercase tracking-widest mb-1">Patient / Operator</p>
            <h1 className="text-3xl font-black text-white uppercase tracking-tight leading-none mb-1">
              {data.name || <span className="text-white/20">Unknown</span>}
            </h1>
            <p className="text-[10px] font-black text-brand-light/70 uppercase tracking-widest font-mono">
              ID: {userId}
            </p>
          </div>

          <div className="grid grid-cols-2 gap-3 px-6 pb-4">
            <div className="col-span-2 p-5 rounded-lg bg-red-500/10 border border-red-500/30 flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-red-500/20 flex items-center justify-center flex-shrink-0">
                <Heart size={24} className="text-red-400" />
              </div>
              <div>
                <p className="text-[9px] font-black text-red-400/70 uppercase tracking-widest">Blood Group</p>
                <p className="text-4xl font-black text-red-400 leading-none mt-0.5">
                  {data.blood || <span className="text-red-400/30 text-2xl">Unknown</span>}
                </p>
              </div>
            </div>

            <div className="p-4 rounded-lg bg-brand-light/10 border border-brand-light/20 flex flex-col gap-2">
              <div className="w-8 h-8 rounded-lg bg-brand-light/10 flex items-center justify-center">
                <Car size={16} className="text-brand-light" />
              </div>
              <div>
                <p className="text-[8px] font-semibold text-brand-light/70 uppercase tracking-widest">Vehicle</p>
                <p className="text-sm font-semibold text-white leading-tight mt-0.5">
                  {data.vehicle || <span className="text-white/20">-</span>}
                </p>
              </div>
            </div>

            <div className="p-4 rounded-lg bg-warning/10 border border-warning/20 flex flex-col gap-2">
              <div className="w-8 h-8 rounded-lg bg-amber-500/20 flex items-center justify-center">
                <Phone size={16} className="text-amber-400" />
              </div>
              <div>
                <p className="text-[8px] font-semibold text-amber-400/70 uppercase tracking-widest">SOS Contact</p>
                <p className="text-sm font-semibold text-white leading-tight mt-0.5">
                  {data.contact || <span className="text-white/20">-</span>}
                </p>
              </div>
            </div>
          </div>

          {data.allergies && (
            <div className="mx-6 mb-4 p-4 rounded-lg bg-orange-500/10 border border-orange-500/30 flex items-start gap-3">
              <div className="w-8 h-8 rounded-lg bg-orange-500/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                <Pill size={16} className="text-orange-400" />
              </div>
              <div>
                <p className="text-[8px] font-black text-orange-400/70 uppercase tracking-widest">Known Allergies</p>
                <p className="text-sm font-bold text-orange-300 leading-tight mt-1">{data.allergies}</p>
              </div>
            </div>
          )}

          {data.insurance && (
            <div className="mx-6 mb-4 p-4 rounded-lg bg-brand/10 border border-brand/20 flex items-start gap-3">
              <div className="w-8 h-8 rounded-lg bg-brand/20 flex items-center justify-center flex-shrink-0">
                <FileText size={16} className="text-brand-light" />
              </div>
              <div>
                <p className="text-[8px] font-semibold text-brand-light/70 uppercase tracking-widest">Insurance Provider</p>
                <p className="text-sm font-semibold text-white leading-tight mt-0.5">{data.insurance}</p>
              </div>
            </div>
          )}

          {data.medical && (
            <div className="mx-6 mb-4 p-4 rounded-lg bg-purple-500/10 border border-purple-500/20">
              <p className="text-[8px] font-black text-purple-400/70 uppercase tracking-widest mb-1">Medical Notes</p>
              <p className="text-xs font-medium text-purple-200 leading-relaxed">{data.medical}</p>
            </div>
          )}

          {emergencyContactHref && (
            <div className="px-6 pb-4">
              <a
                href={emergencyContactHref}
                className="flex items-center justify-center gap-2 w-full h-14 rounded-lg bg-brand hover:bg-[#145230] transition-all text-white font-black text-sm uppercase tracking-widest shadow-lg shadow-brand/30 active:scale-95"
              >
                <Phone size={18} />
                Call Emergency Contact
              </a>
            </div>
          )}

          <div className="border-t border-white/5 px-6 py-4">
            <p className="text-[8px] font-semibold text-text-2 uppercase tracking-widest mb-3">India Emergency Lines</p>
            <div className="grid grid-cols-4 gap-2">
              {[
                { label: 'Police', num: '100', color: 'text-brand-light bg-brand-light/10 border-brand-light/20' },
                { label: 'Ambulance', num: '102', color: 'text-red-400 bg-red-400/10 border-red-400/20' },
                { label: 'Fire', num: '101', color: 'text-orange-400 bg-orange-400/10 border-orange-400/20' },
                { label: 'Helpline', num: '112', color: 'text-brand-light bg-brand-light/10 border-brand-light/20' },
              ].map((item) => (
                <a
                  key={item.num}
                  href={`tel:${item.num}`}
                  className={`flex flex-col items-center p-2.5 rounded-xl border ${item.color} transition-all active:scale-95`}
                >
                  <span className="text-lg font-black leading-none">{item.num}</span>
                  <span className="text-[7px] font-bold uppercase tracking-wider opacity-70 mt-0.5">{item.label}</span>
                </a>
              ))}
            </div>
          </div>

          <div className="border-t border-white/5 px-6 py-3 flex items-center justify-between">
            <span className="text-[8px] font-semibold text-text-2 uppercase tracking-widest">
              Powered by SafeVixAI
            </span>
            <div className="flex items-center gap-1">
              <CheckCircle2 size={10} className="text-brand-light" />
              <span className="text-[8px] font-bold text-brand-light uppercase tracking-widest">Verified</span>
            </div>
          </div>
        </div>

        <p className="text-center text-[9px] font-bold text-text-2 uppercase tracking-widest mt-6">
          Scanned from SafeVixAI Emergency QR Card - no login required
        </p>
      </div>
    </div>
  );
}
