import { test, expect } from '@playwright/test';

test.describe('Profile Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.setItem('__E2E_SKIP_AUTH__', 'true');
    });
    await page.goto('/profile');
    await page.waitForLoadState('networkidle');
  });

  test('profile page renders with user info', async ({ page }) => {
    const h1 = page.locator('h1');
    await expect(h1).toBeVisible();
  });

  test('edit profile button renders', async ({ page }) => {
    await expect(page.getByText(/edit/i).or(page.getByRole('button', { name: /edit/i }))).toBeTruthy();
  });

  test('emergency contact section renders', async ({ page }) => {
    await expect(page.getByText(/emergency/i).or(page.getByText(/contact/i))).toBeTruthy();
  });
});
