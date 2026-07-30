// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

import {
  getOrCreateGuestId,
  getGuestProfile,
  updateGuestProfile,
  isGuestMode,
  clearGuestSession,
} from '../guest-auth';

describe('Guest Auth (Progressive Auth)', function() {
  beforeEach(function() {
    localStorage.clear();
  });

  it('getOrCreateGuestId should create a persistent ID', function() {
    const id = getOrCreateGuestId();
    expect(id).toBeTruthy();
    expect(id.length).toBe(32);
    const id2 = getOrCreateGuestId();
    expect(id2).toBe(id);
  });

  it('getGuestProfile should return null for new session', function() {
    expect(getGuestProfile()).toBeNull();
  });

  it('getGuestProfile should return profile after creation', function() {
    getOrCreateGuestId();
    const profile = getGuestProfile();
    expect(profile).not.toBeNull();
    expect(profile!.id).toBeTruthy();
    expect(profile!.createdAt).toBeGreaterThan(0);
  });

  it('updateGuestProfile should merge fields', function() {
    getOrCreateGuestId();
    updateGuestProfile({ bloodGroup: 'O+', preferredLanguage: 'hi' });
    const profile = getGuestProfile();
    expect(profile!.bloodGroup).toBe('O+');
    expect(profile!.preferredLanguage).toBe('hi');
  });

  it('updateGuestProfile should not overwrite existing fields', function() {
    getOrCreateGuestId();
    updateGuestProfile({ bloodGroup: 'O+' });
    updateGuestProfile({ preferredLanguage: 'ta' });
    const profile = getGuestProfile();
    expect(profile!.bloodGroup).toBe('O+');
    expect(profile!.preferredLanguage).toBe('ta');
  });

  it('isGuestMode should return true after ID creation', function() {
    expect(isGuestMode()).toBe(false);
    getOrCreateGuestId();
    expect(isGuestMode()).toBe(true);
  });

  it('clearGuestSession should remove all guest data', function() {
    getOrCreateGuestId();
    clearGuestSession();
    expect(isGuestMode()).toBe(false);
    expect(getGuestProfile()).toBeNull();
  });

  it('generated IDs should be unique', function() {
    const ids = new Set<string>();
    for (let i = 0; i < 100; i++) {
      ids.add(getOrCreateGuestId());
      localStorage.clear();
    }
    expect(ids.size).toBe(100);
  });
});


