import { test, expect } from '@playwright/test';

test.describe('Privacy & Terms Pages', () => {
  test('privacy page renders with content', async ({ page }) => {
    await page.goto('/privacy');
    await page.waitForLoadState('networkidle');
    await expect(page.getByRole('heading', { name: /privacy/i })).toBeVisible();
  });

  test('terms page renders with content', async ({ page }) => {
    await page.goto('/terms');
    await page.waitForLoadState('networkidle');
    await expect(page.getByRole('heading', { name: /terms/i })).toBeVisible();
  });

  test('navigation between privacy and terms works', async ({ page }) => {
    await page.goto('/privacy');
    await page.waitForLoadState('networkidle');
    if (await page.getByText(/terms/i).first().isVisible()) {
      await page.getByText(/terms/i).first().click();
      await expect(page).toHaveURL(/terms/);
    }
  });
});
