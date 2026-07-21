// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

import { openDB } from 'idb';
import type { UserProfile } from './store';

const DB_NAME = 'safevix-profile-db';
const STORE_NAME = 'profiles';
const PROFILE_KEY = 'primary';
const LEGACY_STORAGE_KEY = 'svai-storage';

/* istanbul ignore next */const isBrowser = () => typeof window !== 'undefined' && 'indexedDB' in window;

export async function openProfileDb() {
  /* istanbul ignore next */
  if (!isBrowser()) return null;
  return openDB(DB_NAME, 1, {
    /* istanbul ignore next */
    upgrade(db) {
      if (!db.objectStoreNames.contains(STORE_NAME)) {
        db.createObjectStore(STORE_NAME);
      }
    },
  });
}

export async function saveUserProfileToIndexedDB(profile: UserProfile) {
  const db = await openProfileDb();
  if (!db) return;
  await db.put(STORE_NAME, profile, PROFILE_KEY);
}

export async function loadUserProfileFromIndexedDB(): Promise<UserProfile | null> {
  const db = await openProfileDb();
  if (!db) return null;
  return (await db.get(STORE_NAME, PROFILE_KEY)) ?? null;
}

export async function migrateUserProfileFromLocalStorage() {
  if (!isBrowser()) return;

  const raw = window.localStorage.getItem(LEGACY_STORAGE_KEY);
  if (!raw) return;

  try {
    const parsed = JSON.parse(raw) as { state?: { userProfile?: UserProfile } };
    const profile = parsed.state?.userProfile;
    if (profile && Object.values(profile).some(Boolean)) {
      await saveUserProfileToIndexedDB(profile);
    }

    if (parsed.state && 'userProfile' in parsed.state) {
      delete parsed.state.userProfile;
      window.localStorage.setItem(LEGACY_STORAGE_KEY, JSON.stringify(parsed));
    }
  } catch {
    // Leave malformed legacy state untouched; Zustand can still recover defaults.
  }
}
