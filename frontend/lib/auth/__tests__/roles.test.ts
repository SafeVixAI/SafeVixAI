// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

import {
  getPermissionsForRole,
  hasPermission,
  hasAnyPermission,
  hasAllPermissions,
  isPublicRoute,
  getRequiredPermissionsForRoute,
  canAccessRoute,
  Role,
  AuthUser,
  Permission,
} from '../roles';

const citizenUser: AuthUser = {
  id: 'cit1',
  name: 'Citizen One',
  role: 'citizen',
  permissions: getPermissionsForRole('citizen'),
};

const officerUser: AuthUser = {
  id: 'off1',
  name: 'Officer One',
  role: 'officer',
  permissions: getPermissionsForRole('officer'),
};

const adminUser: AuthUser = {
  id: 'adm1',
  name: 'Admin One',
  role: 'admin',
  permissions: getPermissionsForRole('admin'),
};

const superAdminUser: AuthUser = {
  id: 'sup1',
  name: 'Super Admin One',
  role: 'super_admin',
  permissions: getPermissionsForRole('super_admin'),
};

describe('getPermissionsForRole', function() {
  it('should return citizen permissions', function() {
    const perms = getPermissionsForRole('citizen');
    expect(perms).toContain('emergency:sos');
    expect(perms).toContain('challan:calculate');
    expect(perms).toContain('assistant:chat');
    expect(perms).toContain('assistant:offline');
    expect(perms).toContain('settings:view');
    expect(perms).not.toContain('report:resolve');
    expect(perms).not.toContain('admin:users_view');
    expect(perms).not.toContain('admin:roles_manage');
  });

  it('should return officer permissions', function() {
    const perms = getPermissionsForRole('officer');
    expect(perms).toContain('report:resolve');
    expect(perms).toContain('emergency:sos');
    expect(perms).toContain('tracking:view');
    expect(perms).not.toContain('assistant:offline');
    expect(perms).not.toContain('admin:users_view');
  });

  it('should return admin permissions', function() {
    const perms = getPermissionsForRole('admin');
    expect(perms).toContain('admin:users_view');
    expect(perms).toContain('admin:users_manage');
    expect(perms).toContain('admin:analytics_view');
    expect(perms).toContain('admin:system_config');
    expect(perms).toContain('admin:audit_logs');
    expect(perms).toContain('assistant:offline');
    expect(perms).not.toContain('admin:roles_manage');
  });

  it('should return super_admin permissions', function() {
    const perms = getPermissionsForRole('super_admin');
    expect(perms).toContain('admin:roles_manage');
    expect(perms).toContain('admin:users_view');
    expect(perms).toContain('admin:users_manage');
    expect(perms).toContain('admin:analytics_view');
    expect(perms).toContain('admin:system_config');
    expect(perms).toContain('admin:audit_logs');
  });

  it('should return undefined for unknown role', function() {
    const perms = getPermissionsForRole('unknown_role' as Role);
    expect(perms).toBeUndefined();
  });
});

describe('hasPermission', function() {
  it('should return true when user has the permission', function() {
    expect(hasPermission(citizenUser, 'emergency:sos')).toBe(true);
    expect(hasPermission(officerUser, 'report:resolve')).toBe(true);
    expect(hasPermission(adminUser, 'admin:users_view')).toBe(true);
    expect(hasPermission(superAdminUser, 'admin:roles_manage')).toBe(true);
  });

  it('should return false when user lacks the permission', function() {
    expect(hasPermission(citizenUser, 'report:resolve')).toBe(false);
    expect(hasPermission(officerUser, 'assistant:offline')).toBe(false);
    expect(hasPermission(adminUser, 'admin:roles_manage')).toBe(false);
  });

  it('should return false for null user', function() {
    expect(hasPermission(null, 'emergency:sos')).toBe(false);
  });
});

describe('hasAnyPermission', function() {
  it('should return true when user has at least one permission', function() {
    expect(hasAnyPermission(citizenUser, ['admin:users_view', 'emergency:sos'])).toBe(true);
    expect(hasAnyPermission(officerUser, ['report:resolve', 'admin:roles_manage'])).toBe(true);
  });

  it('should return false when user has none of the permissions', function() {
    expect(hasAnyPermission(citizenUser, ['report:resolve', 'admin:users_view'])).toBe(false);
  });

  it('should return false for empty permissions array', function() {
    expect(hasAnyPermission(citizenUser, [])).toBe(false);
  });

  it('should return false for null user', function() {
    expect(hasAnyPermission(null, ['emergency:sos'])).toBe(false);
  });
});

describe('hasAllPermissions', function() {
  it('should return true when user has all permissions', function() {
    expect(hasAllPermissions(citizenUser, ['emergency:sos', 'challan:calculate'])).toBe(true);
    expect(hasAllPermissions(adminUser, ['admin:users_view', 'admin:system_config'])).toBe(true);
  });

  it('should return false when user is missing any permission', function() {
    expect(hasAllPermissions(citizenUser, ['emergency:sos', 'report:resolve'])).toBe(false);
    expect(hasAllPermissions(officerUser, ['report:resolve', 'assistant:offline'])).toBe(false);
  });

  it('should return true for empty permissions array', function() {
    expect(hasAllPermissions(citizenUser, [])).toBe(true);
  });

  it('should return false for null user', function() {
    expect(hasAllPermissions(null, ['emergency:sos'])).toBe(false);
  });
});

describe('isPublicRoute', function() {
  it('should return true for exact public route paths', function() {
    expect(isPublicRoute('/login')).toBe(true);
    expect(isPublicRoute('/signup')).toBe(true);
    expect(isPublicRoute('/forgot-password')).toBe(true);
    expect(isPublicRoute('/reset-password')).toBe(true);
    expect(isPublicRoute('/landing')).toBe(true);
    expect(isPublicRoute('/privacy')).toBe(true);
    expect(isPublicRoute('/terms')).toBe(true);
    expect(isPublicRoute('/emergency-card')).toBe(true);
    expect(isPublicRoute('/track')).toBe(true);
  });

  it('should return true for subpaths of public routes', function() {
    expect(isPublicRoute('/emergency-card/user123')).toBe(true);
    expect(isPublicRoute('/track/session_abc')).toBe(true);
  });

  it('should return false for non-public routes', function() {
    expect(isPublicRoute('/admin')).toBe(false);
    expect(isPublicRoute('/profile')).toBe(false);
    expect(isPublicRoute('/challan')).toBe(false);
    expect(isPublicRoute('/report')).toBe(false);
    expect(isPublicRoute('/settings')).toBe(false);
  });

  it('should return false for similar looking but not matching routes', function() {
    expect(isPublicRoute('/login-extra')).toBe(false);
    expect(isPublicRoute('/landing-page')).toBe(false);
  });
});

describe('getRequiredPermissionsForRoute', function() {
  it('should return permissions for exact matching route', function() {
    const perms = getRequiredPermissionsForRoute('/admin');
    expect(perms).toEqual(['admin:users_view']);
  });

  it('should return permissions for matching subpath', function() {
    const perms = getRequiredPermissionsForRoute('/admin/users');
    expect(perms).toEqual(['admin:users_view']);
  });

  it('should return permissions for nested subpaths', function() {
    const perms = getRequiredPermissionsForRoute('/admin/users/123');
    expect(perms).toEqual(['admin:users_view']);
  });

  it('should return permissions for admin sub-routes', function() {
    expect(getRequiredPermissionsForRoute('/admin/roles')).toEqual(['admin:users_view']);
    expect(getRequiredPermissionsForRoute('/admin/analytics')).toEqual(['admin:users_view']);
    expect(getRequiredPermissionsForRoute('/admin/settings')).toEqual(['admin:users_view']);
    expect(getRequiredPermissionsForRoute('/admin/audit')).toEqual(['admin:users_view']);
  });

  it('should return permissions for officer route', function() {
    expect(getRequiredPermissionsForRoute('/officer')).toEqual(['report:resolve']);
    expect(getRequiredPermissionsForRoute('/officer/reports')).toEqual(['report:resolve']);
  });

  it('should return null for routes without required permissions', function() {
    expect(getRequiredPermissionsForRoute('/some-random-path')).toBeNull();
    expect(getRequiredPermissionsForRoute('/')).toBeNull();
  });

  it('should return null for public routes', function() {
    expect(getRequiredPermissionsForRoute('/login')).toBeNull();
    expect(getRequiredPermissionsForRoute('/signup')).toBeNull();
  });
});

describe('canAccessRoute', function() {
  it('should allow access to public routes for null user', function() {
    expect(canAccessRoute(null, '/login')).toBe(true);
    expect(canAccessRoute(null, '/landing')).toBe(true);
    expect(canAccessRoute(null, '/privacy')).toBe(true);
  });

  it('should allow access to public routes for any user', function() {
    expect(canAccessRoute(citizenUser, '/login')).toBe(true);
    expect(canAccessRoute(officerUser, '/terms')).toBe(true);
    expect(canAccessRoute(adminUser, '/forgot-password')).toBe(true);
  });

  it('should allow access to routes with no required permissions', function() {
    expect(canAccessRoute(citizenUser, '/')).toBe(true);
    expect(canAccessRoute(citizenUser, '/some-unknown-route')).toBe(true);
  });

  it('should deny access to protected route when user lacks permissions', function() {
    expect(canAccessRoute(citizenUser, '/admin')).toBe(false);
    expect(canAccessRoute(citizenUser, '/officer')).toBe(false);
    expect(canAccessRoute(officerUser, '/admin')).toBe(false);
  });

  it('should allow access to protected route when user has permissions', function() {
    expect(canAccessRoute(adminUser, '/admin')).toBe(true);
    expect(canAccessRoute(officerUser, '/officer')).toBe(true);
    expect(canAccessRoute(adminUser, '/admin/users')).toBe(true);
    expect(canAccessRoute(adminUser, '/admin/analytics')).toBe(true);
    expect(canAccessRoute(superAdminUser, '/admin/roles')).toBe(true);
  });

  it('should deny access for null user to protected routes', function() {
    expect(canAccessRoute(null, '/admin')).toBe(false);
    expect(canAccessRoute(null, '/officer')).toBe(false);
    expect(canAccessRoute(null, '/profile')).toBe(false);
  });

  it('should allow citizen to access their own routes', function() {
    expect(canAccessRoute(citizenUser, '/challan')).toBe(true);
    expect(canAccessRoute(citizenUser, '/report')).toBe(true);
    expect(canAccessRoute(citizenUser, '/profile')).toBe(true);
    expect(canAccessRoute(citizenUser, '/settings')).toBe(true);
  });
});

describe('Role hierarchy', function() {
  it('super_admin should have all admin permissions plus admin:roles_manage', function() {
    const supPerms = getPermissionsForRole('super_admin');
    const adminPerms = getPermissionsForRole('admin');
    adminPerms.forEach(function(p) {
      expect(supPerms).toContain(p);
    });
    expect(supPerms).toContain('admin:roles_manage');
  });

  it('citizen should not have officer/admin permissions', function() {
    const citizenPerms = getPermissionsForRole('citizen');
    expect(citizenPerms).not.toContain('report:resolve');
    expect(citizenPerms).not.toContain('admin:users_view');
    expect(citizenPerms).not.toContain('admin:roles_manage');
  });

  it('officer should have report:resolve but not offline assistant', function() {
    const offPerms = getPermissionsForRole('officer');
    expect(offPerms).toContain('report:resolve');
    expect(offPerms).not.toContain('assistant:offline');
    expect(offPerms).not.toContain('admin:users_view');
  });

  it('admin should not have admin:roles_manage', function() {
    const adminPerms = getPermissionsForRole('admin');
    expect(adminPerms).not.toContain('admin:roles_manage');
  });

  it('all roles should have emergency:sos', function() {
    const roles: Role[] = ['citizen', 'officer', 'admin', 'super_admin'];
    roles.forEach(function(role) {
      const perms = getPermissionsForRole(role);
      expect(perms).toContain('emergency:sos');
    });
  });
});

describe('Edge cases', function() {
  it('should handle user with empty permissions array', function() {
    const emptyPermUser: AuthUser = { id: 'empty', name: 'Empty', role: 'citizen', permissions: [] };
    expect(hasPermission(emptyPermUser, 'emergency:sos')).toBe(false);
    expect(hasAnyPermission(emptyPermUser, ['emergency:sos'])).toBe(false);
    expect(hasAllPermissions(emptyPermUser, [])).toBe(true);
  });

  it('should throw if permissions property is missing', function() {
    const malformedUser = {} as AuthUser;
    expect(function() { hasPermission(malformedUser, 'emergency:sos' as Permission); }).toThrow();
  });

  it('hasPermission should be case sensitive for permission names', function() {
    const found = citizenUser.permissions.includes('Emergency:SOS' as Permission);
    expect(found).toBe(false);
    expect(hasPermission(citizenUser, 'Emergency:SOS' as Permission)).toBe(false);
  });

  it('canAccessRoute should handle empty pathname', function() {
    expect(canAccessRoute(citizenUser, '')).toBe(true);
    expect(canAccessRoute(null, '')).toBe(true);
  });

  it('getPermissionsForRole should handle invalid role input', function() {
    expect(getPermissionsForRole('' as Role)).toBeUndefined();
    expect(getPermissionsForRole('ADMIN' as Role)).toBeUndefined();
  });

  it('public routes constant should not be mutated by isPublicRoute', function() {
    expect(isPublicRoute('/login')).toBe(true);
    expect(isPublicRoute('/login')).toBe(true);
  });

  it('multiple permissions check should work with overlapping roles', function() {
    expect(hasAnyPermission(adminUser, ['admin:roles_manage', 'emergency:sos'])).toBe(true);
    expect(hasAllPermissions(adminUser, ['emergency:sos', 'admin:users_view'])).toBe(true);
  });
});

describe('null user guards', function() {
  it('hasPermission should handle null', function() {
    expect(hasPermission(null, 'emergency:sos')).toBe(false);
  });

  it('hasAnyPermission should handle null', function() {
    expect(hasAnyPermission(null, ['emergency:sos'])).toBe(false);
  });

  it('hasAllPermissions should handle null', function() {
    expect(hasAllPermissions(null, ['emergency:sos'])).toBe(false);
  });

  it('canAccessRoute should handle null for protected routes', function() {
    expect(canAccessRoute(null, '/admin')).toBe(false);
  });

  it('canAccessRoute should handle null for public routes', function() {
    expect(canAccessRoute(null, '/login')).toBe(true);
  });
});
