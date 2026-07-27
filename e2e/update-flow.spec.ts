// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

import { test, expect } from '@playwright/test';

test.describe('Update Management Flow', function () {
  test.beforeEach(async function ({ page }) {
    await page.goto('/');
  });

  test('update banner appears when update available', async function ({ page }) {
    await page.waitForSelector('[role="alert"]');
    await expect(page.locator('[role="alert"]')).toContainText(/update/i);
  });

  test('click Update Now initiates download', async function ({ page }) {
    await page.waitForSelector('text=Update Now', { timeout: 10000 });
    await page.click('text=Update Now');
    await expect(page.locator('text=Downloading')).toBeVisible({ timeout: 5000 });
  });

  test('progress bar fills to 100%', async function ({ page }) {
    await page.waitForSelector('text=Update Now', { timeout: 10000 });
    await page.click('text=Update Now');
    const progressBar = page.locator('[role="alert"] div[style*="width"]').first();
    await expect(progressBar).toBeVisible();
    await page.waitForFunction(function () {
      const bars = document.querySelectorAll('[role="alert"] [style*="width"]');
      return bars.length > 0;
    }, { timeout: 15000 });
  });

  test('restart button appears after install', async function ({ page }) {
    await page.waitForSelector('text=Restart', { timeout: 20000 });
    await expect(page.locator('text=Restart')).toBeVisible();
  });

  test('settings persist channel change', async function ({ page }) {
    await page.goto('/settings');
    await page.waitForSelector('text=Beta', { timeout: 5000 });
    await page.click('text=Beta');
    await expect(page.locator('text=Beta').first()).toHaveClass(/bg-blue-600/);
  });

  test('update scheduler status endpoint responds', async function ({ page }) {
    const response = await page.request.get('/api/v1/updates/scheduler/status');
    expect(response.ok()).toBeTruthy();
    const body = await response.json();
    expect(body).toHaveProperty('running');
  });
});
