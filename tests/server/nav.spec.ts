import { test, expect } from './fixtures';

test('nav bar is visible on home page', async ({ page }) => {
	await page.goto('/');
	await expect(page.locator('nav')).toBeVisible();
	await expect(page.locator('nav a[href="/"]')).toContainText('Cash Compass');
});

test('nav links to accounts and categories from home', async ({ page }) => {
	await page.goto('/');
	const hamburger = page.locator('[onclick*="mobile-nav"]');
	if (await hamburger.isVisible()) {
		await hamburger.click();
		await expect(page.locator('#mobile-nav a[href="/accounts"]')).toBeVisible();
		await expect(page.locator('#mobile-nav a[href="/categories"]')).toBeVisible();
	} else {
		await expect(page.locator('nav a[href="/accounts"]').first()).toBeVisible();
		await expect(page.locator('nav a[href="/categories"]').first()).toBeVisible();
	}
});

test('accounts link is active on accounts page', async ({ page }) => {
	await page.goto('/accounts');
	const accountsLink = page.locator('nav a[href="/accounts"]').first();
	await expect(accountsLink).toHaveClass(/text-emerald-400/);
	const categoriesLink = page.locator('nav a[href="/categories"]').first();
	await expect(categoriesLink).not.toHaveClass(/text-emerald-400/);
});

test('categories link is active on categories page', async ({ page }) => {
	await page.goto('/categories');
	const categoriesLink = page.locator('nav a[href="/categories"]').first();
	await expect(categoriesLink).toHaveClass(/text-emerald-400/);
	const accountsLink = page.locator('nav a[href="/accounts"]').first();
	await expect(accountsLink).not.toHaveClass(/text-emerald-400/);
});

test('nav brand link navigates to dashboard', async ({ page }) => {
	await page.goto('/accounts');
	await page.locator('nav a[href="/"]').click();
	await expect(page).toHaveURL('/dashboard');
});

test('nav accounts link navigates to accounts', async ({ page }) => {
	await page.goto('/');
	const hamburger = page.locator('[onclick*="mobile-nav"]');
	if (await hamburger.isVisible()) {
		await hamburger.click();
		await page.locator('#mobile-nav a[href="/accounts"]').click();
	} else {
		await page.locator('nav a[href="/accounts"]').first().click();
	}
	await expect(page).toHaveURL('/accounts');
});
