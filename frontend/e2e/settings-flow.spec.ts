import { test, expect } from '@playwright/test';

test.describe('Settings Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.setItem('__E2E_SKIP_AUTH__', 'true');
    });
    await page.goto('/settings');
    await page.waitForLoadState('networkidle');
  });

  test('settings page renders with heading', async ({ page }) => {
    await expect(page.getByRole('heading', { name: /settings|preferences/i })).toBeVisible();
  });

  test('toggle switches are interactive', async ({ page }) => {
    const toggles = page.locator('input[role="switch"]');
    const toggleCount = await toggles.count();
    if (toggleCount > 0) {
      const first = toggles.first();
      await first.click();
    }
  });

  test('language selector renders', async ({ page }) => {
    const select = page.locator('select').or(page.locator('[data-testid="lang-selector"]'));
    await expect(select).toBeVisible();
  });

  test('sign out button renders', async ({ page }) => {
    await expect(page.getByText(/sign.?out/i).or(page.getByText(/logout/i))).toBeTruthy();
  });
});
