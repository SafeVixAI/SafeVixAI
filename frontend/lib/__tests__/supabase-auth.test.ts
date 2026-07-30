// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

import { getSupabaseBrowserClient } from '../supabase-auth';

describe('getSupabaseBrowserClient', function() {

  beforeEach(function() {
    process.env.NEXT_PUBLIC_SUPABASE_URL = 'https://testproject.supabase.co';
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test';
  });

  afterEach(function() {
    delete process.env.NEXT_PUBLIC_SUPABASE_URL;
    delete process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
  });

  describe('success path', function() {

    it('returns a SupabaseClient when env vars are set', function() {
      const client = getSupabaseBrowserClient();
      expect(client).not.toBeNull();
    });

    it('returns same instance on repeated calls (singleton)', function() {
      const a = getSupabaseBrowserClient();
      const b = getSupabaseBrowserClient();
      expect(a).toBe(b);
    });

    it('returned client has auth methods', function() {
      const client = getSupabaseBrowserClient()!;
      expect(client.auth).toBeDefined();
      expect(typeof client.auth.signUp).toBe('function');
      expect(typeof client.auth.signInWithPassword).toBe('function');
      expect(typeof client.auth.signOut).toBe('function');
      expect(typeof client.auth.getSession).toBe('function');
      expect(typeof client.auth.onAuthStateChange).toBe('function');
    });

  });

  describe('missing env vars', function() {

    it('returns null when NEXT_PUBLIC_SUPABASE_URL is missing', function() {
      let mod: typeof import('../supabase-auth');
      jest.isolateModules(function() {
        delete process.env.NEXT_PUBLIC_SUPABASE_URL;
        mod = require('../supabase-auth');
      });
      expect(mod!.getSupabaseBrowserClient()).toBeNull();
    });

    it('returns null when NEXT_PUBLIC_SUPABASE_ANON_KEY is missing', function() {
      let mod: typeof import('../supabase-auth');
      jest.isolateModules(function() {
        delete process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
        mod = require('../supabase-auth');
      });
      expect(mod!.getSupabaseBrowserClient()).toBeNull();
    });

  });

  describe('placeholder values', function() {

    it('returns null when URL contains YOUR_PROJECT_REF', function() {
      let mod: typeof import('../supabase-auth');
      jest.isolateModules(function() {
        process.env.NEXT_PUBLIC_SUPABASE_URL = 'https://YOUR_PROJECT_REF.supabase.co';
        mod = require('../supabase-auth');
      });
      expect(mod!.getSupabaseBrowserClient()).toBeNull();
    });

    it('returns null when anon key contains YOUR_', function() {
      let mod: typeof import('../supabase-auth');
      jest.isolateModules(function() {
        process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY = 'YOUR_ANON_KEY';
        mod = require('../supabase-auth');
      });
      expect(mod!.getSupabaseBrowserClient()).toBeNull();
    });

  });

  describe('edge cases', function() {

    it('returns null when URL is empty string', function() {
      let mod: typeof import('../supabase-auth');
      jest.isolateModules(function() {
        process.env.NEXT_PUBLIC_SUPABASE_URL = '';
        mod = require('../supabase-auth');
      });
      expect(mod!.getSupabaseBrowserClient()).toBeNull();
    });

    it('returns null when anon key is empty string', function() {
      let mod: typeof import('../supabase-auth');
      jest.isolateModules(function() {
        process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY = '';
        mod = require('../supabase-auth');
      });
      expect(mod!.getSupabaseBrowserClient()).toBeNull();
    });

    it('returns null when both are undefined', function() {
      let mod: typeof import('../supabase-auth');
      jest.isolateModules(function() {
        delete process.env.NEXT_PUBLIC_SUPABASE_URL;
        delete process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
        mod = require('../supabase-auth');
      });
      expect(mod!.getSupabaseBrowserClient()).toBeNull();
    });

    it('trims whitespace from URL', function() {
      let mod: typeof import('../supabase-auth');
      jest.isolateModules(function() {
        process.env.NEXT_PUBLIC_SUPABASE_URL = '  https://testproject.supabase.co  ';
        mod = require('../supabase-auth');
      });
      expect(mod!.getSupabaseBrowserClient()).not.toBeNull();
    });

    it('trims whitespace from anon key', function() {
      let mod: typeof import('../supabase-auth');
      jest.isolateModules(function() {
        process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY = '  eyJhbGciOiJIUzI1NiJ9.test  ';
        mod = require('../supabase-auth');
      });
      expect(mod!.getSupabaseBrowserClient()).not.toBeNull();
    });

  });

  describe('session management', function() {

    it('getSession returns session data on success', async function() {
      const client = getSupabaseBrowserClient()!;
      const mockSession = { user: { id: 'u1' }, access_token: 'tok1' };
      client.auth.getSession = jest.fn().mockResolvedValue({
        data: { session: mockSession },
        error: null,
      });
      const result = await client.auth.getSession();
      expect(result.data.session).toEqual(mockSession);
      expect(result.error).toBeNull();
    });

    it('getSession returns null when no active session', async function() {
      const client = getSupabaseBrowserClient()!;
      client.auth.getSession = jest.fn().mockResolvedValue({
        data: { session: null },
        error: null,
      });
      const result = await client.auth.getSession();
      expect(result.data.session).toBeNull();
    });

    it('signUp creates a new user', async function() {
      const client = getSupabaseBrowserClient()!;
      const mockUser = { id: 'u2', email: 'test@example.com' };
      client.auth.signUp = jest.fn().mockResolvedValue({
        data: { user: mockUser, session: null },
        error: null,
      });
      const result = await client.auth.signUp({
        email: 'test@example.com',
        password: 'password123',
      });
      expect(result.data.user).toEqual(mockUser);
      expect(result.error).toBeNull();
    });

    it('signUp returns error on failure', async function() {
      const client = getSupabaseBrowserClient()!;
      client.auth.signUp = jest.fn().mockResolvedValue({
        data: { user: null, session: null },
        error: { message: 'User already registered', status: 422 },
      });
      const result = await client.auth.signUp({
        email: 'exists@example.com',
        password: 'password123',
      });
      expect(result.data.user).toBeNull();
      expect(result.error).not.toBeNull();
      expect(result.error.message).toBe('User already registered');
    });

    it('signInWithPassword logs in existing user', async function() {
      const client = getSupabaseBrowserClient()!;
      const mockSession = { user: { id: 'u1', email: 'a@b.com' }, access_token: 'tok' };
      client.auth.signInWithPassword = jest.fn().mockResolvedValue({
        data: { user: mockSession.user, session: mockSession },
        error: null,
      });
      const result = await client.auth.signInWithPassword({
        email: 'a@b.com',
        password: 'secret',
      });
      expect(result.data.user.email).toBe('a@b.com');
      expect(result.error).toBeNull();
    });

    it('signInWithPassword returns error on wrong credentials', async function() {
      const client = getSupabaseBrowserClient()!;
      client.auth.signInWithPassword = jest.fn().mockResolvedValue({
        data: { user: null, session: null },
        error: { message: 'Invalid login credentials', status: 400 },
      });
      const result = await client.auth.signInWithPassword({
        email: 'wrong@example.com',
        password: 'bad',
      });
      expect(result.data.user).toBeNull();
      expect(result.error.message).toBe('Invalid login credentials');
    });

    it('signOut clears session', async function() {
      const client = getSupabaseBrowserClient()!;
      client.auth.signOut = jest.fn().mockResolvedValue({
        error: null,
      });
      const result = await client.auth.signOut();
      expect(result.error).toBeNull();
    });

    it('signOut returns error when sign out fails', async function() {
      const client = getSupabaseBrowserClient()!;
      client.auth.signOut = jest.fn().mockResolvedValue({
        error: { message: 'Session not found', status: 401 },
      });
      const result = await client.auth.signOut();
      expect(result.error).not.toBeNull();
      expect(result.error.message).toBe('Session not found');
    });

    it('onAuthStateChange listens to auth events', function() {
      const client = getSupabaseBrowserClient()!;
      const unsubscribe = jest.fn();
      client.auth.onAuthStateChange = jest.fn(function() {
        return { data: { subscription: { unsubscribe: unsubscribe } } };
      });
      const listener = jest.fn();
      const sub = client.auth.onAuthStateChange(listener);
      expect(sub.data.subscription.unsubscribe).toBeDefined();
      sub.data.subscription.unsubscribe();
      expect(unsubscribe).toHaveBeenCalled();
    });

    it('handles expired token gracefully', async function() {
      const client = getSupabaseBrowserClient()!;
      client.auth.getSession = jest.fn().mockResolvedValue({
        data: { session: null },
        error: { message: 'JWT expired', status: 401 },
      });
      const result = await client.auth.getSession();
      expect(result.data.session).toBeNull();
      expect(result.error.message).toBe('JWT expired');
    });

    it('handles network error', async function() {
      const client = getSupabaseBrowserClient()!;
      client.auth.signInWithPassword = jest.fn().mockRejectedValue(
        new TypeError('Failed to fetch'),
      );
      await expect(
        client.auth.signInWithPassword({ email: 'a@b.com', password: 'x' }),
      ).rejects.toThrow('Failed to fetch');
    });

  });

});
