'use client';

// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team


import React, { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import {
  Shield, KeyRound, AlertTriangle,
  CheckCircle2, Mail, Wifi, ArrowLeft,
} from 'lucide-react';
import { getSupabaseBrowserClient } from '@/lib/supabase-auth';
import { useAppStore } from '@/lib/store';
import { usePageEntry } from '@/hooks/usePageEntry';
import { useShallow } from 'zustand/react/shallow';
import { useFormValidation } from '@/lib/use-form-validation';
import { RESET_RULES } from '@/lib/validation-schemas';
import { Logo } from '@/components/ui/Logo';

export default function ForgotPasswordPage() {
  const router = useRouter();
  const { isAuthenticated } = useAppStore(useShallow((s) => ({ isAuthenticated: s.isAuthenticated })));
  const pageRef = usePageEntry();

  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [scanLine, setScanLine] = useState(0);
  const emailRef = useRef<HTMLInputElement>(null);

  const { errors, handleChange, handleBlur, handleSubmit: formSubmit } = useFormValidation(RESET_RULES);

  // Redirect if already authenticated
  useEffect(() => {
    if (isAuthenticated) router.replace('/');
  }, [isAuthenticated, router]);

  // Animate scan line
  useEffect(() => {
    const id = setInterval(() => setScanLine(p => (p + 1) % 100), 50);
    return () => clearInterval(id);
  }, []);

  useEffect(() => {
    document.title = 'Reset Password | SafeVixAI';
    emailRef.current?.focus();
  }, []);

  const handleReset = async (e: React.FormEvent) => {
    e.preventDefault();
    const values = { email };
    const canSubmit = await formSubmit(values, async () => {
      setError('');
      setSuccess('');
      setLoading(true);
      try {
        const supabase = getSupabaseBrowserClient();
        if (supabase) {
          const { error: resetError } = await supabase.auth.resetPasswordForEmail(
            email.trim().toLowerCase(),
            { redirectTo: `${window.location.origin}/auth/callback?type=recovery` }
          );

          if (resetError) {
            throw resetError;
          }
        }

        // Always show success (security — don't reveal if email exists)
        setSuccess('If an account exists for that email, a reset link has been sent.');
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : 'Something went wrong';
        // Still show generic success for security
        if (msg.includes('rate limit') || msg.includes('Too many')) {
          setError('Too many requests. Please try again in a few minutes.');
        } else {
          setSuccess('If an account exists for that email, a reset link has been sent.');
        }
      } finally {
        setLoading(false);
      }
    });
    if (!canSubmit) return;
  };

  return (
    <div ref={pageRef} className="relative min-h-screen w-full bg-bg flex items-center justify-center overflow-hidden">

      {/* ── Tactical Background ── */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-[-20%] right-[-10%] w-[60%] h-[60%] rounded-full bg-brand/20 blur-[120px]" />
        <div className="absolute bottom-[-20%] left-[-10%] w-[50%] h-[50%] rounded-full bg-brand-light/10 blur-[100px]" />
        <div
          className="absolute left-0 right-0 h-[1px] bg-gradient-to-r from-transparent via-brand-light/40 to-transparent transition-none pointer-events-none"
          style={{ top: `${scanLine}%` }}
        />
      </div>

      {/* ── Main Panel ── */}
      <div className="relative w-full max-w-md mx-4">
        <div className="relative rounded-xl border border-white/10 bg-surface-1/90 backdrop-blur-2xl overflow-hidden shadow-2xl shadow-black/60">
          {/* Top accent bar */}
          <div className="h-1 bg-gradient-to-r from-brand via-brand-light to-brand" />

          <div className="p-8">
            {/* Logo + Brand */}
            <div className="flex flex-col items-center gap-4 mb-8">
              <Logo size={68} status="online" />
              <div className="text-center">
                <h1 className="text-2xl font-black text-white tracking-tight font-space uppercase">
                  SafeVixAI
                </h1>
                <p className="text-[10px] font-bold text-brand-light uppercase tracking-[0.1em] mt-0.5">
                  Password Recovery
                </p>
              </div>

              <p className="text-sm text-text-2 text-center max-w-xs leading-relaxed">
                Enter your operator email and we&apos;ll send you a secure link to reset your access key.
              </p>
            </div>

            {/* ── Reset Form ── */}
            <form onSubmit={handleReset} className="flex flex-col gap-4" noValidate>

              {/* Email */}
              <div className="flex flex-col gap-1.5">
                <label htmlFor="forgot-email" className="text-[9px] font-semibold text-text-3 uppercase tracking-[0.25em] pl-1">
                  Operator Email
                </label>
                <div className="relative">
                  <Mail size={15} className="absolute left-4 top-1/2 -translate-y-1/2 text-text-4 pointer-events-none" />
                  <input
                    id="forgot-email"
                    ref={emailRef}
                    type="email"
                    autoComplete="email"
                    aria-required="true"
                    aria-invalid={errors.email ? 'true' : undefined}
                    aria-describedby={errors.email ? 'forgot-email-error' : undefined}
                    value={email}
                    onChange={e => { setEmail(e.target.value); handleChange('email', e.target.value); setError(''); setSuccess(''); }}
                    onBlur={e => handleBlur('email', e.target.value)}
                    placeholder="operator@safevixai.app"
                    className={`w-full h-12 pl-11 pr-4 rounded-xl bg-white/5 border text-white placeholder:text-text-3 text-sm font-medium focus:outline-none focus:ring-1 transition-all ${errors.email ? 'border-red-500/60 focus:border-red-500 focus:ring-red-500/30' : 'border-white/10 focus:border-brand focus:ring-brand/40'}`}
                  />
                  {errors.email && <p id="forgot-email-error" role="alert" className="text-[10px] font-semibold text-red-400 px-1 mt-0.5">{errors.email}</p>}
                </div>
              </div>

              {/* Error / Success messages */}
              {error && (
                <div className="flex items-center gap-2.5 px-4 py-3 rounded-xl bg-red-500/10 border border-red-500/20">
                  <AlertTriangle size={14} className="text-red-400 flex-shrink-0" />
                  <span className="text-[12px] font-bold text-red-400">{error}</span>
                </div>
              )}
              {success && (
                <div className="flex items-center gap-2.5 px-4 py-3 rounded-xl bg-brand-light/10 border border-brand-light/20">
                  <CheckCircle2 size={14} className="text-brand-light flex-shrink-0" />
                  <span className="text-[12px] font-bold text-brand-light">{success}</span>
                </div>
              )}

              {/* Submit Button */}
              <button
                type="submit"
                disabled={loading || !!success}
                className="relative h-13 w-full rounded-xl bg-brand hover:bg-[#145230] disabled:opacity-60 disabled:cursor-not-allowed border border-brand/40 text-white font-black text-sm uppercase tracking-widest transition-all shadow-lg shadow-brand/20 overflow-hidden flex items-center justify-center gap-2 mt-1"
                style={{ height: '52px' }}
              >
                <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/5 to-transparent -skew-x-12" />
                {loading ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    <span>Sending...</span>
                  </>
                ) : (
                  <>
                    <KeyRound size={16} />
                    <span>Send Reset Link</span>
                  </>
                )}
              </button>
            </form>

            {/* Back to login */}
            <div className="text-center mt-6">
              <Link
                href="/login"
                className="inline-flex items-center gap-1.5 text-xs font-semibold text-brand-light hover:text-white transition-colors"
              >
                <ArrowLeft size={12} />
                Back to Login
              </Link>
            </div>
          </div>

          {/* Footer */}
          <div className="border-t border-white/5 px-8 py-3 flex items-center justify-between">
            <div className="flex items-center gap-1.5">
              <Shield size={10} className="text-brand" />
              <span className="text-[8px] font-semibold text-text-3 uppercase tracking-[0.1em]">
                SafeVixAI Sentinel Protocol
              </span>
            </div>
            <div className="flex items-center gap-1">
              <Wifi size={9} className="text-brand-light" />
              <span className="text-[8px] font-bold text-brand-light uppercase tracking-widest">Secure</span>
            </div>
          </div>
        </div>

        <p className="text-center text-[9px] font-bold text-text-3 uppercase tracking-[0.1em] mt-5">
          SafeVixAI v2.4 · IIT Madras Hackathon 2026
        </p>
      </div>
    </div>
  );
}