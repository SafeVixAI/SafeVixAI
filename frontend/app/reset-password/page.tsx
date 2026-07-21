'use client';

// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team


import React, { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import {
  Shield, Eye, EyeOff, KeyRound, AlertTriangle,
  CheckCircle2, Lock, ArrowLeft, Wifi,
} from 'lucide-react';
import { getSupabaseBrowserClient } from '@/lib/supabase-auth';
import { useAppStore } from '@/lib/store';
import { usePageEntry } from '@/hooks/usePageEntry';
import { useShallow } from 'zustand/react/shallow';
import { Logo } from '@/components/ui/Logo';
import { PUBLIC_API_BASE_URL } from '@/lib/public-env';

export default function ResetPasswordPage() {
  const router = useRouter();
  const { isAuthenticated } = useAppStore(useShallow((s) => ({ isAuthenticated: s.isAuthenticated })));
  const pageRef = usePageEntry();

  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPwd, setShowPwd] = useState(false);
  const [showConfirmPwd, setShowConfirmPwd] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [scanLine, setScanLine] = useState(0);
  const pwdRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (isAuthenticated) router.replace('/');
  }, [isAuthenticated, router]);

  useEffect(() => {
    const id = setInterval(() => setScanLine(p => (p + 1) % 100), 50);
    return () => clearInterval(id);
  }, []);

  useEffect(() => {
    document.title = 'Reset Password | SafeVixAI';
    pwdRef.current?.focus();
  }, []);

  const handleReset = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!password || password.length < 8) {
      setError('Password must be at least 8 characters');
      return;
    }
    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    setError('');
    setLoading(true);

    try {
      const supabase = getSupabaseBrowserClient();
      if (supabase) {
        const { error: updateError } = await supabase.auth.updateUser({ password });
        if (!updateError) {
          setSuccess(true);
          setTimeout(() => router.push('/login'), 2500);
          return;
        }
      }

      const res = await fetch(`${PUBLIC_API_BASE_URL}/api/v1/auth/reset-password`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ password }),
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || 'Password reset failed');
      }

      setSuccess(true);
      setTimeout(() => router.push('/login'), 2500);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Something went wrong';
      if (msg.includes('rate limit') || msg.includes('Too many')) {
        setError('Too many requests. Please try again in a few minutes.');
      } else {
        setError(msg);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div ref={pageRef} className="relative min-h-screen w-full bg-bg flex items-center justify-center overflow-hidden">
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-[-20%] right-[-10%] w-[60%] h-[60%] rounded-full bg-brand/20 blur-[120px]" />
        <div className="absolute bottom-[-20%] left-[-10%] w-[50%] h-[50%] rounded-full bg-brand-light/10 blur-[100px]" />
        <div
          className="absolute left-0 right-0 h-[1px] bg-gradient-to-r from-transparent via-brand-light/40 to-transparent transition-none pointer-events-none"
          style={{ top: `${scanLine}%` }}
        />
      </div>

      <div className="relative w-full max-w-md mx-4">
        <div className="relative rounded-xl border border-white/10 bg-surface-1/90 backdrop-blur-2xl overflow-hidden shadow-2xl shadow-black/60">
          <div className="h-1 bg-gradient-to-r from-brand via-brand-light to-brand" />

          <div className="p-8">
            <div className="flex flex-col items-center gap-4 mb-8">
              <Logo size={68} status="online" />
              <div className="text-center">
                <h1 className="text-2xl font-black text-white tracking-tight font-space uppercase">
                  SafeVixAI
                </h1>
                <p className="text-[10px] font-bold text-brand-light uppercase tracking-[0.1em] mt-0.5">
                  Set New Password
                </p>
              </div>

              <p className="text-sm text-text-2 text-center max-w-xs leading-relaxed">
                Choose a new access key for your operator account.
              </p>
            </div>

            {success ? (
              <div className="flex flex-col items-center gap-4 py-6">
                <CheckCircle2 size={48} className="text-brand-light" />
                <p className="text-brand-light font-bold text-sm">Password updated successfully!</p>
                <p className="text-text-3 text-xs">Redirecting to login...</p>
              </div>
            ) : (
              <form onSubmit={handleReset} className="flex flex-col gap-4" noValidate>
                <div className="flex flex-col gap-1.5">
                  <label htmlFor="reset-password" className="text-[9px] font-semibold text-text-3 uppercase tracking-[0.25em] pl-1">
                    New Access Key
                  </label>
                  <div className="relative">
                    <Lock size={15} className="absolute left-4 top-1/2 -translate-y-1/2 text-text-4 pointer-events-none" />
                    <input
                      id="reset-password"
                      ref={pwdRef}
                      type={showPwd ? 'text' : 'password'}
                      autoComplete="new-password"
                      aria-required="true"
                      aria-invalid={error ? 'true' : undefined}
                      value={password}
                      onChange={e => { setPassword(e.target.value); setError(''); }}
                      placeholder="Min 8 characters"
                      className="w-full h-12 pl-11 pr-12 rounded-xl bg-white/5 border border-white/10 text-white placeholder:text-text-3 text-sm font-medium focus:outline-none focus:ring-1 focus:border-brand focus:ring-brand/40 transition-all"
                    />
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

                <div className="flex flex-col gap-1.5">
                  <label htmlFor="reset-confirm-password" className="text-[9px] font-semibold text-text-3 uppercase tracking-[0.25em] pl-1">
                    Confirm Access Key
                  </label>
                  <div className="relative">
                    <Lock size={15} className="absolute left-4 top-1/2 -translate-y-1/2 text-text-4 pointer-events-none" />
                    <input
                      id="reset-confirm-password"
                      type={showConfirmPwd ? 'text' : 'password'}
                      autoComplete="new-password"
                      aria-required="true"
                      aria-invalid={error ? 'true' : undefined}
                      value={confirmPassword}
                      onChange={e => { setConfirmPassword(e.target.value); setError(''); }}
                      placeholder="Re-enter access key"
                      className="w-full h-12 pl-11 pr-12 rounded-xl bg-white/5 border border-white/10 text-white placeholder:text-text-3 text-sm font-medium focus:outline-none focus:ring-1 focus:border-brand focus:ring-brand/40 transition-all"
                    />
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

                {error && (
                  <div role="alert" className="flex items-center gap-2.5 px-4 py-3 rounded-xl bg-red-500/10 border border-red-500/20">
                    <AlertTriangle size={14} className="text-red-400 flex-shrink-0" />
                    <span className="text-[12px] font-bold text-red-400">{error}</span>
                  </div>
                )}

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
                      <span>Updating...</span>
                    </>
                  ) : (
                    <>
                      <KeyRound size={16} />
                      <span>Update Password</span>
                    </>
                  )}
                </button>
              </form>
            )}

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