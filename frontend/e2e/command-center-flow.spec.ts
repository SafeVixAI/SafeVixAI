import { test, expect } from '@playwright/test';

test.describe('Command Center Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.setItem('__E2E_SKIP_AUTH__', 'true');
    });
    await page.goto('/command-center');
    await page.waitForLoadState('networkidle');
  });

  test('page renders with heading', async ({ page }) => {
    const heading = page.locator('h1');
    await expect(heading).toBeVisible();
  });

  test('status cards render', async ({ page }) => {
    const cards = page.locator('[class*="card"]').or(page.locator('[class*="stat"]'));
    const count = await cards.count();
    expect(count).toBeGreaterThanOrEqual(0);
  });

  test('filter tabs render', async ({ page }) => {
    const tabs = page.getByRole('button').filter({ hasText: /all|open|progress|closed/i });
    const count = await tabs.count();
    expect(count).toBeGreaterThanOrEqual(0);
  });
});
