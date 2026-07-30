// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

jest.mock('@/lib/store', function() {
  const actual = jest.requireActual('zustand');
  const create = actual.create;
  let mockedSet: (partial: object) => void;
  const store = create(function(set: (partial: object) => void) {
    mockedSet = set;
    return {
      isAuthenticated: false,
      operatorName: '',
      authToken: null,
      authRole: 'citizen',
      userProfile: { id: '', name: '', phone: '', bloodGroup: '', vehicleNumber: '', emergencyContact: '', emergencyContacts: [], medicalConditions: '', preferredLanguage: 'en' },
      setAuth: function(name: string, token?: string, role?: string) {
        mockedSet({ isAuthenticated: true, operatorName: name, authToken: token || null, authRole: role || 'citizen' });
      },
      clearAuth: function() {
        mockedSet({ isAuthenticated: false, operatorName: '', authToken: null, authRole: 'citizen' });
      },
      setAuthToken: function(token: string | null) {
        mockedSet({ authToken: token });
      },
      setAuthRole: function(role: string) {
        mockedSet({ authRole: role });
      },
      setUserProfile: function(profile: object) {
        mockedSet({ userProfile: profile });
      },
      setProfileHydrated: function() {},
    };
  });
  return { useAppStore: store };
});

import { renderHook } from '@testing-library/react';
import { useAuth } from '../use-auth';
import { useAppStore } from '@/lib/store';

describe('useAuth', function() {
  beforeEach(function() {
    useAppStore.setState({
      isAuthenticated: false,
      operatorName: '',
      authToken: null,
      authRole: 'citizen',
      userProfile: { id: '', name: '', phone: '', bloodGroup: '', vehicleNumber: '', emergencyContact: '', emergencyContacts: [], medicalConditions: '', preferredLanguage: 'en' },
    });
  });

  describe('unauthenticated state', function() {
    let result: ReturnType<typeof renderHook>;

    beforeEach(function() {
      result = renderHook(function() { return useAuth(); });
    });

    it('returns isAuthenticated as false', function() {
      expect(result.result.current.isAuthenticated).toBe(false);
    });

    it('returns user as null', function() {
      expect(result.result.current.user).toBeNull();
    });

    it('returns authToken as null', function() {
      expect(result.result.current.authToken).toBeNull();
    });

    it('defaults role to citizen', function() {
      expect(result.result.current.role).toBe('citizen');
    });

    it('can() returns false for any permission', function() {
      expect(result.result.current.can('emergency:sos')).toBe(false);
    });

    it('canAny() returns false', function() {
      expect(result.result.current.canAny(['emergency:sos', 'admin:users_view'])).toBe(false);
    });

    it('canAll() returns false', function() {
      expect(result.result.current.canAll(['emergency:sos', 'challan:calculate'])).toBe(false);
    });

    it('allows access to public routes', function() {
      expect(result.result.current.canAccess('/login')).toBe(true);
      expect(result.result.current.canAccess('/signup')).toBe(true);
    });
  });

  describe('authenticated state', function() {
    let result: ReturnType<typeof renderHook>;

    beforeEach(function() {
      useAppStore.getState().setAuth('Test User', 'jwt-token-xyz', 'citizen');
      result = renderHook(function() { return useAuth(); });
    });

    it('returns isAuthenticated as true', function() {
      expect(result.result.current.isAuthenticated).toBe(true);
    });

    it('returns user object with name', function() {
      expect(result.result.current.user).not.toBeNull();
      expect(result.result.current.user?.name).toBe('Test User');
    });

    it('returns user with citizen role and permissions', function() {
      expect(result.result.current.user?.role).toBe('citizen');
      expect(result.result.current.user?.permissions).toContain('emergency:sos');
      expect(result.result.current.user?.permissions).toContain('challan:calculate');
      expect(result.result.current.user?.permissions).not.toContain('admin:users_view');
    });

    it('returns authToken', function() {
      expect(result.result.current.authToken).toBe('jwt-token-xyz');
    });

    it('returns role from store', function() {
      expect(result.result.current.role).toBe('citizen');
    });

    it('can() checks permission correctly', function() {
      expect(result.result.current.can('emergency:sos')).toBe(true);
      expect(result.result.current.can('admin:users_view')).toBe(false);
    });

    it('canAny() returns true if any permission matches', function() {
      expect(result.result.current.canAny(['admin:users_view', 'emergency:sos'])).toBe(true);
      expect(result.result.current.canAny(['admin:users_view', 'admin:users_manage'])).toBe(false);
    });

    it('canAll() returns true only if all permissions match', function() {
      expect(result.result.current.canAll(['emergency:sos', 'challan:calculate'])).toBe(true);
      expect(result.result.current.canAll(['emergency:sos', 'admin:users_view'])).toBe(false);
    });
  });

  describe('role-based access', function() {
    it('grants admin permissions when role is admin', function() {
      useAppStore.getState().setAuth('Admin User', 'token', 'admin');
      const { result } = renderHook(function() { return useAuth(); });
      expect(result.current.user?.permissions).toContain('admin:users_view');
      expect(result.current.user?.permissions).toContain('admin:users_manage');
      expect(result.current.user?.permissions).toContain('admin:analytics_view');
    });

    it('grants super_admin permissions including roles_manage', function() {
      useAppStore.getState().setAuth('Super User', 'token', 'super_admin');
      const { result } = renderHook(function() { return useAuth(); });
      expect(result.current.user?.permissions).toContain('admin:roles_manage');
      expect(result.current.user?.permissions).toContain('admin:system_config');
      expect(result.current.user?.permissions).toContain('admin:audit_logs');
    });

    it('officer has report:resolve but not admin permissions', function() {
      useAppStore.getState().setAuth('Officer', 'token', 'officer');
      const { result } = renderHook(function() { return useAuth(); });
      expect(result.current.can('report:resolve')).toBe(true);
      expect(result.current.can('admin:users_view')).toBe(false);
    });
  });

  describe('canAccess route checking', function() {
    it('allows public routes for unauthenticated users', function() {
      const { result } = renderHook(function() { return useAuth(); });
      expect(result.current.canAccess('/login')).toBe(true);
      expect(result.current.canAccess('/landing')).toBe(true);
    });

    it('allows route matching user permissions', function() {
      useAppStore.getState().setAuth('Citizen', 'token', 'citizen');
      const { result } = renderHook(function() { return useAuth(); });
      expect(result.current.canAccess('/challan')).toBe(true);
      expect(result.current.canAccess('/report')).toBe(true);
    });

    it('denies route when user lacks required permission', function() {
      useAppStore.getState().setAuth('Citizen', 'token', 'citizen');
      const { result } = renderHook(function() { return useAuth(); });
      expect(result.current.canAccess('/admin')).toBe(false);
      expect(result.current.canAccess('/officer')).toBe(false);
    });

    it('allows admin route for admin user', function() {
      useAppStore.getState().setAuth('Admin', 'token', 'admin');
      const { result } = renderHook(function() { return useAuth(); });
      expect(result.current.canAccess('/admin')).toBe(true);
      expect(result.current.canAccess('/admin/users')).toBe(true);
    });

    it('allows unknown routes (no permission mapping)', function() {
      const { result } = renderHook(function() { return useAuth(); });
      expect(result.current.canAccess('/some-random-page')).toBe(true);
    });
  });

  describe('reactive updates', function() {
    it('reactively sets user to null when auth is cleared', function() {
      useAppStore.getState().setAuth('User', 'token', 'citizen');
      const { result, rerender } = renderHook(function() { return useAuth(); });
      expect(result.current.user).not.toBeNull();
      useAppStore.getState().clearAuth();
      rerender();
      expect(result.current.user).toBeNull();
      expect(result.current.isAuthenticated).toBe(false);
    });

    it('reactively updates user when role changes', function() {
      useAppStore.getState().setAuth('User', 'token', 'citizen');
      const { result, rerender } = renderHook(function() { return useAuth(); });
      expect(result.current.can('admin:users_view')).toBe(false);
      useAppStore.getState().setAuthRole('admin');
      rerender();
      expect(result.current.user?.role).toBe('admin');
      expect(result.current.can('admin:users_view')).toBe(true);
    });

    it('reactively updates user when operatorName changes', function() {
      useAppStore.getState().setAuth('Old Name', 'token', 'citizen');
      const { result, rerender } = renderHook(function() { return useAuth(); });
      expect(result.current.user?.name).toBe('Old Name');
      useAppStore.getState().setAuth('New Name', 'token', 'citizen');
      rerender();
      expect(result.current.user?.name).toBe('New Name');
    });
  });
});
