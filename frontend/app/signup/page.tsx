'use client';

// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team


import React, { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import {
  Shield, Eye, EyeOff, UserPlus, AlertTriangle,
  CheckCircle2, Lock, Mail, User, Wifi,
} from 'lucide-react';
import { PUBLIC_API_BASE_URL } from '@/lib/public-env';
import { getSupabaseBrowserClient } from '@/lib/supabase-auth';
import { useAppStore } from '@/lib/store';
import { usePageEntry } from '@/hooks/usePageEntry';
import { useShallow } from 'zustand/react/shallow';
import { useFormValidation } from '@/lib/use-form-validation';
import { SIGNUP_RULES } from '@/lib/validation-schemas';
import { Logo } from '@/components/ui/Logo';

const API_URL = PUBLIC_API_BASE_URL;

export default function SignupPage() {
  const router = useRouter();
  const { isAuthenticated } = useAppStore(useShallow((s) => ({ isAuthenticated: s.isAuthenticated })));
  const pageRef = usePageEntry();

  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPwd, setShowPwd] = useState(false);
  const [showConfirmPwd, setShowConfirmPwd] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [scanLine, setScanLine] = useState(0);
  const nameRef = useRef<HTMLInputElement>(null);

  const { errors, handleChange, handleBlur, handleSubmit: formSubmit } = useFormValidation(SIGNUP_RULES(password));

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
    document.title = 'Create Account | SafeVixAI';
    nameRef.current?.focus();
  }, []);

  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault();
    const values = { name: fullName, email, password, confirmPassword };
    const canSubmit = await formSubmit(values, async () => {
      setError('');
      setLoading(true);
      try {
        // Try Supabase first
        const supabase = getSupabaseBrowserClient();
        if (supabase) {
          const { error: supabaseError } = await supabase.auth.signUp({
            email: email.trim().toLowerCase(),
            password,
            options: { data: { name: fullName.trim() } },
          });

          if (!supabaseError) {
            setSuccess('Account created! Check your email to verify.');
            setTimeout(() => router.push('/login'), 3000);
            return;
          }
          // If Supabase fails, fall through to FastAPI
          if (supabaseError.message !== 'Signups not allowed for this instance') {
            throw supabaseError;
          }
        }

        // Fallback to FastAPI
        const res = await fetch(`${API_URL}/api/v1/auth/register`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name: fullName.trim(), email: email.trim().toLowerCase(), password }),
        });

        if (!res.ok) {
          const data = await res.json().catch(() => ({}));
          throw new Error(data.detail || 'Registration failed');
        }

        setSuccess('Account created! You can now log in.');
        setTimeout(() => router.push('/login'), 2000);
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : 'Registration failed';
        setError(msg);
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

      {/* ── Main Signup Panel ── */}
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
                  Create Operator Account
                </p>
              </div>

              <div className="flex items-center gap-3">
                <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-brand/20 border border-brand/30">
                  <span className="w-1.5 h-1.5 rounded-full bg-brand-light animate-pulse" />
                  <span className="text-[9px] font-semibold text-brand-light uppercase tracking-widest">Sentinel Online</span>
                </div>
                <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-white/5 border border-white/10">
                  <Lock size={9} className="text-text-2" />
                  <span className="text-[9px] font-semibold text-text-3 uppercase tracking-widest">Encrypted</span>
                </div>
              </div>
            </div>

            {/* ── Auth Form ── */}
            <form onSubmit={handleSignup} className="flex flex-col gap-4" noValidate>

              {/* Full Name */}
              <div className="flex flex-col gap-1.5">
                <label htmlFor="signup-name" className="text-[9px] font-semibold text-text-3 uppercase tracking-[0.25em] pl-1">
                  Full Name
                </label>
                <div className="relative">
                  <User size={15} className="absolute left-4 top-1/2 -translate-y-1/2 text-text-4 pointer-events-none" />
                  <input
                    id="signup-name"
                    ref={nameRef}
                    type="text"
                    autoComplete="name"
                    aria-required="true"
                    aria-invalid={errors.name ? 'true' : undefined}
                    aria-describedby={errors.name ? 'signup-name-error' : undefined}
                    value={fullName}
                    onChange={e => { setFullName(e.target.value); handleChange('name', e.target.value); setError(''); }}
                    onBlur={e => handleBlur('name', e.target.value)}
                    placeholder="Your full name"
                    className={`w-full h-12 pl-11 pr-4 rounded-xl bg-white/5 border text-white placeholder:text-text-3 text-sm font-medium focus:outline-none focus:ring-1 transition-all ${errors.name ? 'border-red-500/60 focus:border-red-500 focus:ring-red-500/30' : 'border-white/10 focus:border-brand focus:ring-brand/40'}`}
                  />
                  {errors.name && <p id="signup-name-error" role="alert" className="text-[10px] font-semibold text-red-400 px-1 mt-0.5">{errors.name}</p>}
                </div>
              </div>

              {/* Email */}
              <div className="flex flex-col gap-1.5">
                <label htmlFor="signup-email" className="text-[9px] font-semibold text-text-3 uppercase tracking-[0.25em] pl-1">
                  Operator Email
                </label>
                <div className="relative">
                  <Mail size={15} className="absolute left-4 top-1/2 -translate-y-1/2 text-text-4 pointer-events-none" />
                  <input
                    id="signup-email"
                    type="email"
                    autoComplete="email"
                    aria-required="true"
                    aria-invalid={errors.email ? 'true' : undefined}
                    aria-describedby={errors.email ? 'signup-email-error' : undefined}
                    value={email}
                    onChange={e => { setEmail(e.target.value); handleChange('email', e.target.value); setError(''); }}
                    onBlur={e => handleBlur('email', e.target.value)}
                    placeholder="operator@safevixai.app"
                    className={`w-full h-12 pl-11 pr-4 rounded-xl bg-white/5 border text-white placeholder:text-text-3 text-sm font-medium focus:outline-none focus:ring-1 transition-all ${errors.email ? 'border-red-500/60 focus:border-red-500 focus:ring-red-500/30' : 'border-white/10 focus:border-brand focus:ring-brand/40'}`}
                  />
                  {errors.email && <p id="signup-email-error" role="alert" className="text-[10px] font-semibold text-red-400 px-1 mt-0.5">{errors.email}</p>}
                </div>
              </div>

              {/* Password */}
              <div className="flex flex-col gap-1.5">
                <label htmlFor="signup-password" className="text-[9px] font-semibold text-text-3 uppercase tracking-[0.25em] pl-1">
                  Access Key
                </label>
                <div className="relative">
                  <Lock size={15} className="absolute left-4 top-1/2 -translate-y-1/2 text-text-4 pointer-events-none" />
                  <input
                    id="signup-password"
                    type={showPwd ? 'text' : 'password'}
                    autoComplete="new-password"
                    aria-required="true"
                    aria-invalid={errors.password ? 'true' : undefined}
                    aria-describedby={errors.password ? 'signup-password-error' : undefined}
                    value={password}
                    onChange={e => { setPassword(e.target.value); handleChange('password', e.target.value); setError(''); }}
                    onBlur={e => handleBlur('password', e.target.value)}
                    placeholder="Min 8 characters"
                    className={`w-full h-12 pl-11 pr-12 rounded-xl bg-white/5 border text-white placeholder:text-text-3 text-sm font-medium focus:outline-none focus:ring-1 transition-all ${errors.password ? 'border-red-500/60 focus:border-red-500 focus:ring-red-500/30' : 'border-white/10 focus:border-brand focus:ring-brand/40'}`}
                  />
                  {errors.password && <p id="signup-password-error" role="alert" className="text-[10px] font-semibold text-red-400 px-1 mt-0.5">{errors.password}</p>}
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

              {/* Confirm Password */}
              <div className="flex flex-col gap-1.5">
                <label htmlFor="signup-confirm-password" className="text-[9px] font-semibold text-text-3 uppercase tracking-[0.25em] pl-1">
                  Confirm Access Key
                </label>
                <div className="relative">
                  <Lock size={15} className="absolute left-4 top-1/2 -translate-y-1/2 text-text-4 pointer-events-none" />
                  <input
                    id="signup-confirm-password"
                    type={showConfirmPwd ? 'text' : 'password'}
                    autoComplete="new-password"
                    aria-required="true"
                    aria-invalid={errors.confirmPassword ? 'true' : undefined}
                    aria-describedby={errors.confirmPassword ? 'signup-confirm-password-error' : undefined}
                    value={confirmPassword}
                    onChange={e => { setConfirmPassword(e.target.value); handleChange('confirmPassword', e.target.value); setError(''); }}
                    onBlur={e => handleBlur('confirmPassword', e.target.value)}
                    placeholder="Re-enter access key"
                    className={`w-full h-12 pl-11 pr-12 rounded-xl bg-white/5 border text-white placeholder:text-text-3 text-sm font-medium focus:outline-none focus:ring-1 transition-all ${errors.confirmPassword ? 'border-red-500/60 focus:border-red-500 focus:ring-red-500/30' : 'border-white/10 focus:border-brand focus:ring-brand/40'}`}
                  />
                  {errors.confirmPassword && <p id="signup-confirm-password-error" role="alert" className="text-[10px] font-semibold text-red-400 px-1 mt-0.5">{errors.confirmPassword}</p>}
                  <button
                    type="button"
                    onClick={() => setShowConfirmPwd(v => !v)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 p-1 text-text-4 hover:text-text-3 transition-colors"
                    aria-label={showConfirmPwd ? 'Hide password' : 'Show password'}
                  >
                    {showConfirmPwd ? <EyeOff size={16} /> : <Eye size={16} />}
                  </button>
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
                disabled={loading}
                className="relative h-13 w-full rounded-xl bg-brand hover:bg-[#145230] disabled:opacity-60 disabled:cursor-not-allowed border border-brand/40 text-white font-black text-sm uppercase tracking-widest transition-all shadow-lg shadow-brand/20 overflow-hidden flex items-center justify-center gap-2 mt-1"
                style={{ height: '52px' }}
              >
                <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/5 to-transparent -skew-x-12" />
                {loading ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    <span>Creating Account...</span>
                  </>
                ) : (
                  <>
                    <UserPlus size={16} />
                    <span>Create Account</span>
                  </>
                )}
              </button>
            </form>

            {/* Login link */}
            <div className="text-center mt-6">
              <span className="text-xs text-text-3">Already have an account? </span>
              <Link href="/login" className="text-xs font-semibold text-brand-light hover:text-white transition-colors">
                Sign In
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