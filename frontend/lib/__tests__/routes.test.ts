// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

import { ROUTES, getRouteConfig, getRouteTitle, getNavRoutes, SOS_HIDDEN_ROUTES } from '../routes';
import type { RouteConfig } from '../routes';

describe('routes', function() {
  describe('ROUTES', function() {
    it('defines 24 routes', function() {
      expect(ROUTES.length).toBe(24);
    });

    it('every route has required string fields', function() {
      ROUTES.forEach(function(r: RouteConfig) {
        expect(typeof r.path).toBe('string');
        expect(typeof r.title).toBe('string');
        expect(typeof r.description).toBe('string');
        expect(r.path.startsWith('/')).toBe(true);
      });
    });

    it('every route has boolean flags', function() {
      ROUTES.forEach(function(r: RouteConfig) {
        expect(typeof r.showInNav).toBe('boolean');
        expect(typeof r.showGlobalSOS).toBe('boolean');
        expect(typeof r.requiresAuth).toBe('boolean');
      });
    });

    it('every route has valid navGroup', function() {
      const validGroups = ['main', 'emergency', 'admin', 'auth'];
      ROUTES.forEach(function(r: RouteConfig) {
        expect(validGroups).toContain(r.navGroup);
      });
    });

    it('dashboard is the first route', function() {
      expect(ROUTES[0].path).toBe('/');
      expect(ROUTES[0].title).toBe('Dashboard');
    });

    it('routes that require permissions also require auth', function() {
      ROUTES.forEach(function(r: RouteConfig) {
        if (r.requiredPermissions) {
          expect(r.requiresAuth).toBe(true);
        }
      });
    });

    it('admin group has requiredPermissions', function() {
      const adminRoutes = ROUTES.filter(function(r: RouteConfig) { return r.navGroup === 'admin'; });
      adminRoutes.forEach(function(r: RouteConfig) {
        expect(Array.isArray(r.requiredPermissions)).toBe(true);
        expect(r.requiredPermissions!.length).toBeGreaterThan(0);
      });
    });

    it('auth group routes do not require auth', function() {
      const authRoutes = ROUTES.filter(function(r: RouteConfig) { return r.navGroup === 'auth'; });
      authRoutes.forEach(function(r: RouteConfig) {
        expect(r.requiresAuth).toBe(false);
      });
    });

    it('path values are unique', function() {
      const paths = ROUTES.map(function(r: RouteConfig) { return r.path; });
      const unique = new Set(paths);
      expect(unique.size).toBe(paths.length);
    });
  });

  describe('getRouteConfig', function() {
    it('returns config for exact path match', function() {
      const config = getRouteConfig('/assistant');
      expect(config).toBeDefined();
      expect(config!.title).toBe('AI Assistant');
    });

    it('returns config for root path', function() {
      const config = getRouteConfig('/');
      expect(config).toBeDefined();
      expect(config!.title).toBe('Dashboard');
    });

    it('matches parent route when path has sub-path', function() {
      const config = getRouteConfig('/guide/some-page');
      expect(config).toBeDefined();
      expect(config!.path).toBe('/guide');
    });

    it('returns undefined for unknown path', function() {
      const config = getRouteConfig('/nonexistent');
      expect(config).toBeUndefined();
    });

    it('returns undefined when no route prefix matches', function() {
      const config = getRouteConfig('/emergency-card/user123');
      expect(config).toBeUndefined();
    });
  });

  describe('getRouteTitle', function() {
    it('returns title for known path', function() {
      expect(getRouteTitle('/sos')).toBe('SOS Emergency');
    });

    it('returns fallback for unknown path', function() {
      expect(getRouteTitle('/bogus')).toBe('SafeVixAI');
    });

    it('returns title for root', function() {
      expect(getRouteTitle('/')).toBe('Dashboard');
    });

    it('returns parent title for sub-path', function() {
      expect(getRouteTitle('/guide/advanced')).toBe('Guide');
    });
  });

  describe('getNavRoutes', function() {
    const navRoutes = ROUTES.filter(function(r: RouteConfig) { return r.showInNav; });
    const navCount = navRoutes.length;

    it('returns all visible nav routes when no group specified', function() {
      const result = getNavRoutes();
      expect(result.length).toBe(navCount);
    });

    it('filters by group: main', function() {
      const result = getNavRoutes('main');
      const expected = navRoutes.filter(function(r: RouteConfig) { return r.navGroup === 'main'; });
      expect(result).toEqual(expected);
    });

    it('filters by group: emergency', function() {
      const result = getNavRoutes('emergency');
      const expected = navRoutes.filter(function(r: RouteConfig) { return r.navGroup === 'emergency'; });
      expect(result).toEqual(expected);
    });

    it('filters by group: admin', function() {
      const result = getNavRoutes('admin');
      const expected = navRoutes.filter(function(r: RouteConfig) { return r.navGroup === 'admin'; });
      expect(result).toEqual(expected);
    });

    it('filters by group: auth', function() {
      const result = getNavRoutes('auth');
      const expected = navRoutes.filter(function(r: RouteConfig) { return r.navGroup === 'auth'; });
      expect(result).toEqual(expected);
    });

    it('showInNav is false for auth group routes', function() {
      const authInNav = ROUTES.filter(function(r: RouteConfig) { return r.navGroup === 'auth' && r.showInNav; });
      expect(authInNav.length).toBe(0);
    });

    it('emergency routes are in nav', function() {
      const emergencyNav = ROUTES.filter(function(r: RouteConfig) { return r.navGroup === 'emergency' && r.showInNav; });
      expect(emergencyNav.length).toBeGreaterThan(0);
    });
  });

  describe('SOS_HIDDEN_ROUTES', function() {
    it('contains paths where showGlobalSOS is false', function() {
      const expected = ROUTES.filter(function(r: RouteConfig) { return !r.showGlobalSOS; }).map(function(r: RouteConfig) { return r.path; });
      expect(SOS_HIDDEN_ROUTES).toEqual(expected);
    });

    it('includes root dashboard path', function() {
      expect(SOS_HIDDEN_ROUTES).toContain('/');
    });

    it('includes login and signup', function() {
      expect(SOS_HIDDEN_ROUTES).toContain('/login');
      expect(SOS_HIDDEN_ROUTES).toContain('/signup');
    });

    it('excludes emergency routes like /locator', function() {
      expect(SOS_HIDDEN_ROUTES).not.toContain('/locator');
    });
  });
});
