'use client';

// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team


import React, { useState, useEffect, useRef } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import {
  Shield, Eye, EyeOff, LogIn, AlertTriangle,
  CheckCircle2, Zap, Lock, Mail, ChevronRight, Wifi,
} from 'lucide-react';
import { PUBLIC_API_BASE_URL } from '@/lib/public-env';
import { getSupabaseBrowserClient } from '@/lib/supabase-auth';
import { useAppStore } from '@/lib/store';
import { usePageEntry } from '@/hooks/usePageEntry';
import { useShallow } from 'zustand/react/shallow';
import { useTranslation } from 'react-i18next';
import { useFormValidation } from '@/lib/use-form-validation';
import { LOGIN_RULES } from '@/lib/validation-schemas';
import { Logo } from '@/components/ui/Logo';

const API_URL = PUBLIC_API_BASE_URL;
const DEMO_CREDS: Array<{ label: string; email: string; password: string; color: string }> = [];

export default function LoginPage() {
  const { t } = useTranslation('auth');
  const router = useRouter();
  const { setAuth, isAuthenticated, setUserProfile } = useAppStore(useShallow((s) => ({ setAuth: s.setAuth, isAuthenticated: s.isAuthenticated, setUserProfile: s.setUserProfile })));
  const pageRef = usePageEntry();
  const searchParams = useSearchParams();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPwd, setShowPwd] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [scanLine, setScanLine] = useState(0);
  const emailRef = useRef<HTMLInputElement>(null);

  const { errors, handleChange, handleBlur, handleSubmit: formSubmit } = useFormValidation(LOGIN_RULES);

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
    document.title = 'Operator Auth | SafeVixAI';
    emailRef.current?.focus();

    // Handle redirect query params from auth callback
    const callbackError = searchParams.get('error');
    const resetStatus = searchParams.get('reset');
    if (callbackError) {
      setError(callbackError);
    } else if (resetStatus === 'success') {
      setSuccess('Password reset successful. Please log in with your new password.');
    }
  }, [searchParams]);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    const values = { email, password };
    const canSubmit = await formSubmit(values, async () => {
      setError('');
      setLoading(true);
      try {
        const supabase = getSupabaseBrowserClient();
        if (supabase) {
          const { data, error: supabaseError } = await supabase.auth.signInWithPassword({
            email: email.trim().toLowerCase(),
            password,
          });

          if (!supabaseError && data.session?.access_token) {
            const displayName =
              (data.user?.user_metadata?.name as string | undefined) ||
              data.user?.email ||
              'SafeVixAI User';
            setAuth(displayName);
            setUserProfile({ name: displayName });
            setSuccess(`Welcome, ${displayName}`);
            setTimeout(() => router.replace('/'), 1200);
            return;
          }
        }

        const res = await fetch(`${API_URL}/api/v1/auth/login`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email: email.trim().toLowerCase(), password }),
        });

        if (!res.ok) {
          const data = await res.json().catch(() => ({}));
          throw new Error(data.detail || 'Invalid credentials');
        }

        const data = await res.json();
        setAuth(data.operator_name);
        setUserProfile({ name: data.operator_name });
        setSuccess(`Welcome, ${data.operator_name}`);
        setTimeout(() => router.replace('/'), 1200);
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : 'Authentication failed';
        setError(msg);
      } finally {
        setLoading(false);
      }
    });
    if (!canSubmit) return;
  };

  const handleDemoMode = () => {
    setError('Demo bypass is disabled. Use the configured operator login.');
  };

  const fillCreds = (c: typeof DEMO_CREDS[0]) => {
    setEmail(c.email);
    setPassword(c.password);
    setError('');
  };

  return (
    <div ref={pageRef} className="relative min-h-screen w-full bg-bg flex items-center justify-center overflow-hidden">

      {/* ── Tactical Background ── */}
      <div className="absolute inset-0 pointer-events-none">
        {/* Spots removed per user request */}
        {/* Top-right green glow */}
        <div className="absolute top-[-20%] right-[-10%] w-[60%] h-[60%] rounded-full bg-brand/20 blur-[120px]" />
        {/* Bottom-left glow */}
        <div className="absolute bottom-[-20%] left-[-10%] w-[50%] h-[50%] rounded-full bg-brand-light/10 blur-[100px]" />

        {/* Animated scan line */}
        <div
          className="absolute left-0 right-0 h-[1px] bg-gradient-to-r from-transparent via-brand-light/40 to-transparent transition-none pointer-events-none"
          style={{ top: `${scanLine}%` }}
        />
      </div>

      {/* ── Main Login Panel ── */}
      <div
        className="relative w-full max-w-md mx-4"
      >

        {/* Card */}
        <div className="relative rounded-xl border border-white/10 bg-surface-1/90 backdrop-blur-2xl overflow-hidden shadow-2xl shadow-black/60">

          {/* Top accent bar */}
          <div className="h-1 bg-gradient-to-r from-brand via-brand-light to-brand" />

          {/* Card Body */}
          <div className="p-8">

            {/* Logo + Brand */}
            <div className="flex flex-col items-center gap-4 mb-8">
              <Logo size={68} status="online" />

              <div className="text-center">
                <h1 className="text-2xl font-black text-white tracking-tight font-space uppercase">
                  {t('common:app_name', 'SafeVixAI')}
                </h1>
                <p className="text-[10px] font-bold text-brand-light uppercase tracking-[0.1em] mt-0.5">
                  {t('operator_authentication', { defaultValue: 'Operator Authentication' })}
                </p>
              </div>

              {/* Status indicators */}
              <div className="flex items-center gap-3">
                <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-brand/20 border border-brand/30">
                  <span className="w-1.5 h-1.5 rounded-full bg-brand-light animate-pulse" />
                  <span className="text-[9px] font-semibold text-brand-light uppercase tracking-widest">{t('sentinel_online', 'Sentinel Online')}</span>
                </div>
                <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-white/5 border border-white/10">
                  <Lock size={9} className="text-text-2" />
                  <span className="text-[9px] font-semibold text-text-3 uppercase tracking-widest">{t('jwt_secured', 'JWT Secured')}</span>
                </div>
              </div>
            </div>

            {/* ── Auth Form ── */}
            <form onSubmit={handleLogin} className="flex flex-col gap-4" noValidate>

              {/* Email */}
              <div className="flex flex-col gap-1.5">
                <label htmlFor="login-email" className="text-[9px] font-semibold text-text-3 uppercase tracking-[0.25em] pl-1">
                  {t('operator_email')}
                </label>
                <div className="relative">
                  <Mail size={15} className="absolute left-4 top-1/2 -translate-y-1/2 text-text-4 pointer-events-none" />
                  <input
                    id="login-email"
                    ref={emailRef}
                    type="email"
                    autoComplete="email"
                    aria-required="true"
                    aria-invalid={errors.email ? 'true' : undefined}
                    aria-describedby={errors.email ? 'login-email-error' : undefined}
                    value={email}
                    onChange={e => { setEmail(e.target.value); handleChange('email', e.target.value); setError(''); }}
                    onBlur={e => handleBlur('email', e.target.value)}
                    placeholder="operator@safevixai.app"
                    className={`w-full h-12 pl-11 pr-4 rounded-xl bg-white/5 border text-white placeholder:text-text-3 text-sm font-medium focus:outline-none focus:ring-1 transition-all ${errors.email ? 'border-red-500/60 focus:border-red-500 focus:ring-red-500/30' : 'border-white/10 focus:border-brand focus:ring-brand/40'}`}
                  />
                  {errors.email && <p id="login-email-error" role="alert" className="text-[10px] font-semibold text-red-400 px-1 mt-0.5">{errors.email}</p>}
                </div>
              </div>

              {/* Password */}
              <div className="flex flex-col gap-1.5">
                <label htmlFor="login-password" className="text-[9px] font-semibold text-text-3 uppercase tracking-[0.25em] pl-1">
                  {t('access_key')}
                </label>
                <div className="relative">
                  <Lock size={15} className="absolute left-4 top-1/2 -translate-y-1/2 text-text-4 pointer-events-none" />
                  <input
                    id="login-password"
                    type={showPwd ? 'text' : 'password'}
                    autoComplete="current-password"
                    aria-required="true"
                    aria-invalid={errors.password ? 'true' : undefined}
                    aria-describedby={errors.password ? 'login-password-error' : undefined}
                    value={password}
                    onChange={e => { setPassword(e.target.value); handleChange('password', e.target.value); setError(''); }}
                    onBlur={e => handleBlur('password', e.target.value)}
                    placeholder="••••••••••••"
                    className={`w-full h-12 pl-11 pr-12 rounded-xl bg-white/5 border text-white placeholder:text-text-3 text-sm font-medium focus:outline-none focus:ring-1 transition-all ${errors.password ? 'border-red-500/60 focus:border-red-500 focus:ring-red-500/30' : 'border-white/10 focus:border-brand focus:ring-brand/40'}`}
                  />
                  {errors.password && <p id="login-password-error" role="alert" className="text-[10px] font-semibold text-red-400 px-1 mt-0.5">{errors.password}</p>}
                  <button
                    type="button"
                    onClick={() => setShowPwd(v => !v)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 p-1 text-text-4 hover:text-text-3 transition-colors"
                    aria-label={showPwd ? 'Hide password' : 'Show password'}
                  >
                    {showPwd ? <EyeOff size={16} /> : <Eye size={16} />}
                  </button>
                </div>
              </div>

              {/* Forgot password link */}
              <div className="flex justify-end -mt-1">
                <Link href="/forgot-password" className="text-[11px] font-semibold text-brand-light hover:text-white transition-colors">
                  Forgot password?
                </Link>
              </div>

              {/* Error / Success messages */}
                              {error && (
                  <div
                    key="error"
                    className="flex items-center gap-2.5 px-4 py-3 rounded-xl bg-red-500/10 border border-red-500/20"
                  >
                    <AlertTriangle size={14} className="text-red-400 flex-shrink-0" />
                    <span className="text-[12px] font-bold text-red-400">{error}</span>
                  </div>
                )}
                {success && (
                  <div
                    key="success"
                    className="flex items-center gap-2.5 px-4 py-3 rounded-xl bg-brand-light/10 border border-brand-light/20"
                  >
                    <CheckCircle2 size={14} className="text-brand-light flex-shrink-0" />
                    <span className="text-[12px] font-bold text-brand-light">{success}</span>
                  </div>
                )}

              {/* Submit Button */}
              <button
                type="submit"
                disabled={loading}
                className="relative h-13 w-full rounded-xl bg-brand hover:bg-[#145230] disabled:opacity-60 disabled:cursor-not-allowed border border-brand/40 text-white font-black text-sm uppercase tracking-widest transition-all shadow-lg shadow-brand/20 overflow-hidden flex items-center justify-center gap-2 mt-1"
                style={{ height: '52px' }}
              >
                {/* Shimmer on hover */}
                <div
                  className="absolute inset-0 bg-gradient-to-r from-transparent via-white/5 to-transparent -skew-x-12"
                />
                {loading ? (
                  <>
                    <div
                      className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full"
                    />
                    <span>{t('authenticating')}</span>
                  </>
                ) : (
                  <>
                    <LogIn size={16} />
                    <span>{t('enter_command_center', 'Enter Command Center')}</span>
                  </>
                )}
              </button>
            </form>

            {/* Create account link */}
            <div className="text-center mt-6">
              <span className="text-xs text-text-3">Don&apos;t have an account? </span>
              <Link href="/signup" className="text-xs font-semibold text-brand-light hover:text-white transition-colors">
                Create one
              </Link>
            </div>

            {/* ── Demo Mode (feature-flagged) ── */}
            {process.env.NEXT_PUBLIC_DEMO_MODE === 'true' && (
              <>
                <div className="flex items-center gap-3 my-5">
                  <div className="flex-1 h-px bg-white/8" />
                  <span className="text-[9px] font-semibold text-text-3 uppercase tracking-widest">or</span>
                  <div className="flex-1 h-px bg-white/8" />
                </div>

                {/* ── Demo Mode Button ── */}
                <button
                  onClick={handleDemoMode}
                  disabled={loading}
                  className="w-full h-12 rounded-xl border border-white/10 bg-white/5 hover:bg-white/8 hover:border-brand/30 transition-all text-text-2 hover:text-white text-[12px] font-black uppercase tracking-widest flex items-center justify-center gap-2 group"
                >
                  <Zap size={14} className="text-brand-light group-hover:animate-pulse" />
                  Demo Mode (Hackathon)
                  <ChevronRight size={13} className="text-text-4 group-hover:text-brand-light group-hover:translate-x-0.5 transition-all" />
                </button>

                {/* ── Quick-fill Demo Credentials ── */}
                <div className="mt-5 flex flex-col gap-2">
                  <p className="text-[8px] font-semibold text-text-3 uppercase tracking-[0.1em] text-center mb-1">
                    {t('demo_credentials', 'Demo Credentials')}
                  </p>
                  <div className="grid grid-cols-2 gap-2">
                    {DEMO_CREDS.map((c) => (
                      <button
                        key={c.email}
                        onClick={() => fillCreds(c)}
                        type="button"
                        className="flex flex-col items-start gap-0.5 px-3 py-2.5 rounded-xl bg-white/5 hover:bg-white/8 border border-white/10 hover:border-brand/30 transition-all text-left"
                      >
                        <span className={`text-[10px] font-semibold uppercase tracking-wide ${c.color}`}>
                          {c.label}
                        </span>
                        <span className="text-[9px] font-mono text-text-4 truncate w-full">{c.email}</span>
                      </button>
                    ))}
                  </div>
                </div>
              </>
            )}
          </div>

          {/* Footer */}
          <div className="border-t border-white/5 px-8 py-3 flex items-center justify-between">
            <div className="flex items-center gap-1.5">
              <Shield size={10} className="text-brand" />
              <span className="text-[8px] font-semibold text-text-3 uppercase tracking-[0.1em]">
                {t('sentinel_protocol', 'SafeVixAI Sentinel Protocol')}
              </span>
            </div>
            <div className="flex items-center gap-1">
              <Wifi size={9} className="text-brand-light" />
              <span className="text-[8px] font-bold text-brand-light uppercase tracking-widest">{t('secure_status', 'Secure')}</span>
            </div>
          </div>
        </div>

        {/* Outside card — version tag */}
        <p className="text-center text-[9px] font-bold text-text-3 uppercase tracking-[0.1em] mt-5">
          {t('hackathon_version_footer', 'SafeVixAI v2.4 · IIT Madras Hackathon 2026')}
        </p>
      </div>
    </div>
  );
}