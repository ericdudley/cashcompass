import { test, expect } from './fixtures';
import { DashboardPage } from './pages/dashboard.page';

test('dashboard page loads', async ({ page }) => {
	const dp = new DashboardPage(page);
	await dp.goto();
	await expect(page.locator('h1')).toContainText('Dashboard');
});

test('home redirects to dashboard', async ({ page }) => {
	await page.goto('/');
	await expect(page).toHaveURL('/dashboard');
});

test('summary stats are visible', async ({ page }) => {
	const dp = new DashboardPage(page);
	await dp.goto();
	await expect(dp.getSummaryStats()).toBeVisible();
	await expect(dp.getStatThisMonth()).toBeVisible();
	await expect(dp.getSummaryStats().locator('text=Monthly Avg')).toBeVisible();
	await expect(dp.getSummaryStats().locator('text=Net Worth')).toBeVisible();
});

test('expenses section is visible', async ({ page }) => {
	const dp = new DashboardPage(page);
	await dp.goto();
	await expect(dp.getExpensesSection()).toBeVisible();
	await expect(dp.getExpensesSection().locator('h2')).toContainText('Expenses');
});

test('net worth section is visible', async ({ page }) => {
	const dp = new DashboardPage(page);
	await dp.goto();
	await expect(dp.getNetWorthSection()).toBeVisible();
	await expect(dp.getNetWorthSection().locator('h2')).toContainText('Net Worth');
});

test('dashboard nav link is active on dashboard page', async ({ page }) => {
	const dp = new DashboardPage(page);
	await dp.goto();
	const dashLink = page.locator('nav a[href="/dashboard"]').first();
	await expect(dashLink).toHaveClass(/text-emerald-400/);
});

test('category table shows rows when expense transactions exist', async ({ page }) => {
	const dp = new DashboardPage(page);
	await dp.goto();

	// If there is expense data (seeded DB), the category table should have rows.
	// If no data, the empty-state message should be present instead.
	const hasTable = await dp.getCategoryTable().isVisible();
	if (hasTable) {
		await expect(dp.getCategoryRows().first()).toBeVisible();
		// Each row must have a non-empty Category cell and a non-empty Total cell
		const firstRow = dp.getCategoryRows().first();
		const cells = firstRow.locator('td');
		await expect(cells.first()).not.toBeEmpty();
		await expect(cells.last()).not.toBeEmpty();
	} else {
		await expect(page.locator('text=No expense data yet')).toBeVisible();
	}
});
