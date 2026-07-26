// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

import { createUpdateSlice } from '../update-slice';

interface TestStore {
  [key: string]: any;
}

function createTestStore() {
  const state: TestStore = {};
  const set = (fn: ((s: TestStore) => Partial<TestStore>) | Partial<TestStore>) => {
    if (typeof fn === 'function') {
      Object.assign(state, fn(state));
    } else {
      Object.assign(state, fn);
    }
  };
  const slice = createUpdateSlice(set);
  Object.assign(state, slice);
  return state;
}

describe('createUpdateSlice', function () {
  test('has default updateInfo', function () {
    const store = createTestStore();
    expect(store.updateInfo).toBeDefined();
    expect(store.updateInfo.currentVersion).toBe('1.0.0');
    expect(store.updateInfo.updateAvailable).toBe(false);
    expect(store.updateInfo.status).toBe('up-to-date');
  });

  test('setUpdateInfo merges partial', function () {
    const store = createTestStore();
    store.setUpdateInfo({ latestVersion: '1.1.0', updateAvailable: true });
    expect(store.updateInfo.latestVersion).toBe('1.1.0');
    expect(store.updateInfo.updateAvailable).toBe(true);
    expect(store.updateInfo.currentVersion).toBe('1.0.0');
  });

  test('setUpdateInfo sets status', function () {
    const store = createTestStore();
    store.setUpdateInfo({ status: 'available' });
    expect(store.updateInfo.status).toBe('available');
  });

  test('dismissUpdateBanner sets flag', function () {
    const store = createTestStore();
    expect(store.updateBannerDismissed).toBe(false);
    store.dismissUpdateBanner();
    expect(store.updateBannerDismissed).toBe(true);
  });

  test('resetUpdateBanner clears flag', function () {
    const store = createTestStore();
    store.dismissUpdateBanner();
    expect(store.updateBannerDismissed).toBe(true);
    store.resetUpdateBanner();
    expect(store.updateBannerDismissed).toBe(false);
  });

  test('setDownloadProgress updates progress', function () {
    const store = createTestStore();
    store.setDownloadProgress(50);
    expect(store.updateInfo.downloadProgress).toBe(50);
  });

  test('setUpdateStatus updates status', function () {
    const store = createTestStore();
    store.setUpdateStatus('downloading');
    expect(store.updateInfo.status).toBe('downloading');
    store.setUpdateStatus('installing');
    expect(store.updateInfo.status).toBe('installing');
  });

  test('updateBannerDismissed defaults to false', function () {
    const store = createTestStore();
    expect(store.updateBannerDismissed).toBe(false);
  });
});
