// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

'use client';

import { useEffect, useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { useAppStore } from '@/lib/store';
import { getSupabaseBrowserClient } from '@/lib/supabase-auth';
import { useShallow } from 'zustand/react/shallow';
import { useHydrated } from '@/lib/use-hydrated';
import { isPublicRoute, canAccessRoute, getPermissionsForRole } from '@/lib/auth/roles';
import type { Role } from '@/lib/auth/roles';

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const nextPathname = usePathname();
  const hydrated = useHydrated();
  const { isAuthenticated, profileHydrated, authRole, setAuth, setUserProfile, setAuthToken, setAuthRole } = useAppStore(
    useShallow((s) => ({
      isAuthenticated: s.isAuthenticated,
      profileHydrated: s.profileHydrated,
      authRole: s.authRole,
      setAuth: s.setAuth,
      setUserProfile: s.setUserProfile,
      setAuthToken: s.setAuthToken,
      setAuthRole: s.setAuthRole,
    }))
  );
  const [checking, setChecking] = useState(true);

  const skipAuth = process.env.NODE_ENV !== 'production' &&
    /* istanbul ignore next */
typeof window !== 'undefined' &&
    window.localStorage.getItem('__E2E_SKIP_AUTH__') === 'true';
  const [isPublic, setIsPublic] = useState(false);

  useEffect(() => {
    if (!nextPathname) return;
    const pathParts = nextPathname.split('/');
    const SUPPORTED_LOCALES = [
      'en', 'hi', 'ta', 'te', 'kn', 'ml', 'mr', 'gu', 'bn', 'pa', 'ur',
      'ar', 'fr', 'es'
    ];
    const firstSegment = pathParts[1];
    const cleanPathname = SUPPORTED_LOCALES.includes(firstSegment)
      ? '/' + pathParts.slice(2).join('/')
      : nextPathname;

    setIsPublic(isPublicRoute(cleanPathname));
  }, [nextPathname]);

  useEffect(() => {
    if (skipAuth || isPublic) return;
    if (!hydrated || !profileHydrated) return;

    async function checkSession() {
      if (isAuthenticated) {
        setChecking(false);
        return;
      }

      const supabase = getSupabaseBrowserClient();
      if (supabase) {
        try {
          const { data: { session } } = await supabase.auth.getSession();
          if (session?.user) {
            const name = (session.user.user_metadata?.name as string) || session.user.email || 'Operator';
            const appRole = (session.user.user_metadata?.role as Role) || 'citizen';
            setAuth(name, session.access_token, appRole);
            setUserProfile({ name });
            setAuthToken(session.access_token);
            setAuthRole(appRole);
            setChecking(false);
            return;
          }
        } catch {
          // Supabase not configured — fall through
        }
      }

      router.replace('/landing');
    }

    checkSession();
  }, [isAuthenticated, hydrated, profileHydrated, router, setAuth, setUserProfile, setAuthToken, skipAuth, isPublic, setAuthRole]);

  const user = isAuthenticated ? {
    id: useAppStore.getState().userProfile.id || 'anonymous',
    name: useAppStore.getState().operatorName || 'User',
    role: authRole,
    permissions: getPermissionsForRole(authRole),
  } : null;

  const canAccess = canAccessRoute(user, nextPathname || '/');

  if (skipAuth || isPublic) {
    return <>{children}</>;
  }

  if (checking && !isAuthenticated) {
    return (
      <div className="min-h-screen bg-bg flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="w-8 h-8 border-2 border-brand-light/30 border-t-brand-light rounded-full animate-spin" />
          <span className="text-xs font-mono text-text-3 uppercase tracking-wider">Verifying session...</span>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) return null;

  if (!canAccess) {
    return (
      <div className="min-h-screen bg-bg flex items-center justify-center">
        <div className="flex flex-col items-center gap-4 text-center max-w-md">
          <div className="w-12 h-12 rounded-full bg-emergency-dim flex items-center justify-center">
            <span className="text-emergency text-xl font-bold">!</span>
          </div>
          <h2 className="text-sm font-bold text-text-1 uppercase tracking-wider">Access Denied</h2>
          <p className="text-xs text-text-2">You do not have the required permissions to access this page.</p>
          <button
            onClick={() => router.push('/')}
            className="mt-2 px-6 py-2 bg-surface-3 hover:bg-surface-4 text-text-1 text-xs font-semibold rounded-lg transition-colors"
          >
            Go to Dashboard
          </button>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}