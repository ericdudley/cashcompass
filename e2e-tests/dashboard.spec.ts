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
	await expect(dp.getStatSelectedExpenses()).toBeVisible();
	await expect(dp.getSummaryStats().locator('text=Selected Expenses')).toBeVisible();
	await expect(dp.getSummaryStats().locator('text=Monthly Avg')).toBeVisible();
	await expect(dp.getSummaryStats().locator('text=Net Worth')).toBeVisible();
});

test('dashboard filters submit as query params', async ({ page }) => {
	const dp = new DashboardPage(page);
	await dp.goto();

	await dp.getFilterTrigger().click();
	await expect(dp.getFilters()).toBeVisible();
	await dp.getFilters().locator('select[name="date_preset"]').selectOption('this_year');
	await dp.getFilters().locator('button[type="submit"]').click();

	await expect(page).toHaveURL(/date_preset=this_year/);
	await dp.getFilterTrigger().click();
	await expect(dp.getFilters().locator('select[name="date_preset"]')).toHaveValue('this_year');
});

test('summary appears before filters on mobile', async ({ page }) => {
	await page.setViewportSize({ width: 390, height: 900 });
	const dp = new DashboardPage(page);
	await dp.goto();

	await expect(dp.getSummaryStats()).toBeVisible();
	await expect(dp.getFilters()).not.toBeVisible();

	const triggerBox = await dp.getFilterTrigger().boundingBox();
	const summaryBox = await dp.getSummaryStats().boundingBox();
	expect(triggerBox).not.toBeNull();
	expect(summaryBox).not.toBeNull();
	expect(summaryBox!.y).toBeGreaterThan(triggerBox!.y);
	expect(summaryBox!.y).toBeLessThan(360);
});

test('dashboard filter menu opens on mobile', async ({ page }) => {
	await page.setViewportSize({ width: 390, height: 900 });
	const dp = new DashboardPage(page);
	await dp.goto();

	await dp.getFilterTrigger().click();

	await expect(dp.getFilters()).toBeVisible();
	await expect(dp.getCategoryFilter().locator('[data-cc-checklist-button]')).toBeVisible();
	await expect(dp.getFilters().locator('button[type="submit"]')).toBeVisible();
});

test('dashboard custom date filters submit as custom range', async ({ page }) => {
	const dp = new DashboardPage(page);
	await dp.goto();

	await dp.getFilterTrigger().click();
	await dp.getFilters().locator('select[name="date_preset"]').selectOption('custom');
	await dp.getFilters().locator('input[name="date_from"]').fill('2026-01-01');
	await dp.getFilters().locator('input[name="date_to"]').fill('2026-02-28');
	await dp.getFilters().locator('button[type="submit"]').click();

	await expect(page).toHaveURL(/date_preset=custom/);
	await expect(page).toHaveURL(/date_from=2026-01-01/);
	await expect(page).toHaveURL(/date_to=2026-02-28/);
});

test('dashboard multi-select filters submit selected values', async ({ page }) => {
	const dp = new DashboardPage(page);
	await dp.goto();

	await dp.getFilterTrigger().click();
	await dp.checkChecklistOption(dp.getExpenseAccountFilter(), 'Daily Expenses');
	await dp.checkChecklistOption(dp.getCategoryFilter(), 'Groceries');
	await expect(dp.getCategoryFilter().locator('[data-cc-checklist-summary]')).toHaveText('Groceries');
	await dp.clearChecklist(dp.getNetWorthAccountFilter());
	await dp.checkChecklistOption(dp.getNetWorthAccountFilter(), 'Savings');
	await dp.getFilters().locator('button[type="submit"]').click();

	await expect(page).toHaveURL(/expense_account_id=3/);
	await expect(page).toHaveURL(/category_id=1/);
	await expect(page).toHaveURL(/net_worth_account_id=2/);
});

test('empty account selections do not fall back to all accounts', async ({ page }) => {
	const dp = new DashboardPage(page);
	await dp.goto();

	await dp.getFilterTrigger().click();
	await dp.clearChecklist(dp.getExpenseAccountFilter());
	await dp.clearChecklist(dp.getNetWorthAccountFilter());
	await dp.getFilters().locator('button[type="submit"]').click();

	await expect(page).toHaveURL(/expense_account_filter=1/);
	await expect(page).toHaveURL(/net_worth_account_filter=1/);
	await expect(page).not.toHaveURL(/expense_account_id=/);
	await expect(page).not.toHaveURL(/net_worth_account_id=/);
	await expect(dp.getStatThisMonth()).toContainText('$0.00');
	await expect(dp.getStatSelectedExpenses()).toContainText('$0.00');
	await expect(dp.getSummaryStats().locator('text=Net Worth').locator('..')).toContainText('$0.00');
});

test('expenses section is visible', async ({ page }) => {
	const dp = new DashboardPage(page);
	await dp.goto();
	await expect(dp.getExpensesSection()).toBeVisible();
	await expect(dp.getExpensesSection().locator('h2')).toContainText('Expenses');
	await expect(dp.getExpenseTrailingAverageLine()).toBeVisible();
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
	await expect(dashLink).toHaveClass(/text-primary/);
	await expect(dashLink).toHaveClass(/font-semibold/);
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

test('expense chart shows hoverable trailing average points and year markers', async ({ page, request }) => {
	const response = await request.post('/settings/import/backup', {
		multipart: {
			file: {
				name: 'expense-history.json',
				mimeType: 'application/json',
				buffer: Buffer.from(JSON.stringify({
					format: 'cashcompass.backup',
					version: 1,
					exported_at: '2027-01-15T12:00:00Z',
					app: { name: 'CashCompass' },
					schema: { entities: ['accounts', 'categories', 'transactions'] },
					accounts: [
						{
							id: 'acct_expenses',
							legacy_numeric_id: 10,
							label: 'Card',
							account_type: 'expenses',
							is_archived: false,
							created_at: '2026-12-01T00:00:00Z',
							updated_at: '2027-01-01T00:00:00Z'
						}
					],
					categories: [
						{
							id: 'cat_food',
							legacy_numeric_id: 20,
							label: 'Food',
							created_at: '2026-12-01T00:00:00Z',
							updated_at: '2027-01-01T00:00:00Z'
						},
						{
							id: 'cat_utilities',
							legacy_numeric_id: 21,
							label: 'Utilities',
							created_at: '2026-12-01T00:00:00Z',
							updated_at: '2027-01-01T00:00:00Z'
						}
					],
					transactions: [
						{
							id: 'txn_dec',
							legacy_numeric_id: 30,
							occurred_at: '2026-12-05',
							amount_cents: -1000,
							label: 'December food',
							account_id: 'acct_expenses',
							category_id: 'cat_food',
							created_at: '2026-12-05T00:00:00Z',
							updated_at: '2026-12-05T00:00:00Z'
						},
						{
							id: 'txn_jan',
							legacy_numeric_id: 31,
							occurred_at: '2027-01-05',
							amount_cents: -2000,
							label: 'January food',
							account_id: 'acct_expenses',
							category_id: 'cat_food',
							created_at: '2027-01-05T00:00:00Z',
							updated_at: '2027-01-05T00:00:00Z'
						},
						{
							id: 'txn_jan_utilities',
							legacy_numeric_id: 32,
							occurred_at: '2027-01-07',
							amount_cents: -500,
							label: 'January utilities',
							account_id: 'acct_expenses',
							category_id: 'cat_utilities',
							created_at: '2027-01-07T00:00:00Z',
							updated_at: '2027-01-07T00:00:00Z'
						}
					]
				}))
			}
		}
	});

	expect(response.ok()).toBeTruthy();

	const dp = new DashboardPage(page);
	await dp.goto();

	await expect(dp.getExpenseTrailingAverageLine()).toBeVisible();
	await expect(dp.getExpenseYearMarkers()).toContainText('2027');
	await expect(dp.getExpenseYearMarkers().locator('[data-year-marker-value="$120.00/yr"]')).toBeVisible();
	await expect(dp.getExpensesSection().locator('[data-expense-segment-label="Food"][data-expense-segment-value="$20.00"]')).toHaveCount(1);
	await expect(dp.getExpensesSection().locator('[data-expense-segment-label="Utilities"][data-expense-segment-value="$5.00"]')).toHaveCount(1);

	const januaryBar = dp.getExpenseBars().filter({ has: page.locator('[data-expense-segment-value="$20.00"]') }).first();
	await expect(januaryBar.locator('[data-bar-total-label="$25"]')).toBeVisible();
	await januaryBar.hover();
	await januaryBar.focus();
	const barTooltip = page.locator('[data-cc-floating-tooltip]');
	await expect(barTooltip).toBeVisible();
	await expect.poll(() => barTooltip.evaluate((el) => getComputedStyle(el).position)).toBe('fixed');
	const tooltipBox = await barTooltip.boundingBox();
	const viewport = page.viewportSize();
	expect(tooltipBox).not.toBeNull();
	expect(viewport).not.toBeNull();
	expect(tooltipBox!.y).toBeGreaterThanOrEqual(8);
	expect(tooltipBox!.y + tooltipBox!.height).toBeLessThanOrEqual(viewport!.height - 8);
	await expect(barTooltip.locator('[data-stacked-bar-label="Total"]')).toContainText('$25.00');
	await expect(barTooltip.locator('[data-stacked-bar-label="Food"]')).toContainText('$20.00');
	await expect(barTooltip.locator('[data-stacked-bar-label="Utilities"]')).toContainText('$5.00');

	const januaryPoint = dp.getExpenseTrailingAveragePoints().locator('[data-trailing-avg-label="$17.50"]');
	await januaryPoint.hover();
	await januaryPoint.focus();
	const tooltip = januaryPoint.locator('span').nth(1);
	await expect.poll(() => tooltip.evaluate((el) => getComputedStyle(el).opacity)).toBe('1');
	await expect(tooltip).toContainText("Jan '27: $17.50");
});

test('dashboard renders imported net worth history as stacked bars', async ({ page, request }) => {
	const response = await request.post('/settings/import/backup', {
		multipart: {
			file: {
				name: 'backup.json',
				mimeType: 'application/json',
				buffer: Buffer.from(JSON.stringify({
					format: 'cashcompass.backup',
					version: 1,
					exported_at: '2027-01-19T12:34:56Z',
					app: { name: 'CashCompass' },
					schema: { entities: ['accounts', 'categories', 'transactions'] },
					accounts: [
						{
							id: 'acct_brokerage',
							legacy_numeric_id: 10,
							label: 'Brokerage',
							account_type: 'net_worth',
							is_archived: false,
							created_at: '2026-12-15T00:00:00Z',
							updated_at: '2027-01-15T23:30:00Z'
						}
					],
					categories: [],
					transactions: [
						{
							id: 'txn_brokerage_1',
							legacy_numeric_id: 20,
							occurred_at: '2026-12-15',
							amount_cents: 100000,
							label: 'Initial balance',
							account_id: 'acct_brokerage',
							category_id: null,
							created_at: '2026-12-15T00:00:00Z',
							updated_at: '2026-12-15T00:00:00Z'
						},
						{
							id: 'txn_brokerage_2',
							legacy_numeric_id: 21,
							occurred_at: '2027-01-15',
							amount_cents: 25050,
							label: 'Growth',
							account_id: 'acct_brokerage',
							category_id: null,
							created_at: '2027-01-15T23:30:00Z',
							updated_at: '2027-01-15T23:30:00Z'
						}
					]
				}))
			}
		}
	});

	expect(response.ok()).toBeTruthy();

	const dp = new DashboardPage(page);
	await dp.goto();

	await expect(dp.getNetWorthSection()).toBeVisible();
	await expect(dp.getNetWorthChart()).toBeVisible();
	await expect(dp.getNetWorthChart().locator('[data-nw-segment-label="Brokerage"][data-nw-segment-value="$1,250.50"]')).toHaveCount(1);
	await expect(dp.getNetWorthYearMarkers()).toContainText('2027');
	await expect(dp.getNetWorthYearMarkers().locator('[data-year-marker-value="$1,000.00"]')).toBeVisible();
	await expect(dp.getNetWorthTrailingAverageLine()).toBeVisible();

	const januaryBar = dp.getNetWorthBars().filter({ has: page.locator('[data-nw-segment-value="$1,250.50"]') }).first();
	await expect(januaryBar.locator('[data-bar-total-label="$1.3k"]')).toBeVisible();
	await januaryBar.hover();
	await januaryBar.focus();
	const tooltip = page.locator('[data-cc-floating-tooltip]');
	await expect(tooltip).toBeVisible();
	await expect.poll(() => tooltip.evaluate((el) => getComputedStyle(el).position)).toBe('fixed');
	await expect(tooltip).toContainText("Jan '27");
	await expect(tooltip).toContainText('Total');
	await expect(tooltip.locator('[data-stacked-bar-label="Brokerage"]')).toContainText('$1,250.50');

	const januaryAveragePoint = dp.getNetWorthTrailingAveragePoints().locator('[data-nw-trailing-avg-label="$1,125.25"]');
	await januaryAveragePoint.hover();
	await januaryAveragePoint.focus();
	const averageTooltip = januaryAveragePoint.locator('span').nth(1);
	await expect.poll(() => averageTooltip.evaluate((el) => getComputedStyle(el).opacity)).toBe('1');
	await expect(averageTooltip).toContainText("Jan '27: $1,125.25");
	await expect(dp.getNetWorthTable()).toContainText('Brokerage');
});

test('long dashboard histories scroll inside charts, not the page', async ({ page, request }) => {
	const monthStarts = Array.from({ length: 240 }, (_, index) => {
		const year = 2024 + Math.floor(index / 12);
		const month = (index % 12) + 1;
		return `${year}-${String(month).padStart(2, '0')}-01`;
	});
	const transactions = monthStarts.flatMap((occurredAt, index) => [
		{
			id: `txn_expense_${index}`,
			legacy_numeric_id: 1000 + index,
			occurred_at: occurredAt,
			amount_cents: -1000 - index,
			label: `Expense ${index}`,
			account_id: 'acct_expenses',
			category_id: 'cat_food',
			created_at: `${occurredAt}T00:00:00Z`,
			updated_at: `${occurredAt}T00:00:00Z`
		},
		{
			id: `txn_net_worth_${index}`,
			legacy_numeric_id: 2000 + index,
			occurred_at: occurredAt,
			amount_cents: 10000,
			label: `Balance ${index}`,
			account_id: 'acct_brokerage',
			category_id: null,
			created_at: `${occurredAt}T00:00:00Z`,
			updated_at: `${occurredAt}T00:00:00Z`
		}
	]);

	const response = await request.post('/settings/import/backup', {
		multipart: {
			file: {
				name: 'long-history.json',
				mimeType: 'application/json',
				buffer: Buffer.from(JSON.stringify({
					format: 'cashcompass.backup',
					version: 1,
					exported_at: '2026-12-31T12:00:00Z',
					app: { name: 'CashCompass' },
					schema: { entities: ['accounts', 'categories', 'transactions'] },
					accounts: [
						{
							id: 'acct_expenses',
							legacy_numeric_id: 10,
							label: 'Card',
							account_type: 'expenses',
							is_archived: false,
							created_at: '2024-01-01T00:00:00Z',
							updated_at: '2026-12-01T00:00:00Z'
						},
						{
							id: 'acct_brokerage',
							legacy_numeric_id: 11,
							label: 'Brokerage',
							account_type: 'net_worth',
							is_archived: false,
							created_at: '2024-01-01T00:00:00Z',
							updated_at: '2026-12-01T00:00:00Z'
						}
					],
					categories: [
						{
							id: 'cat_food',
							legacy_numeric_id: 20,
							label: 'Food',
							created_at: '2024-01-01T00:00:00Z',
							updated_at: '2026-12-01T00:00:00Z'
						}
					],
					transactions
				}))
			}
		}
	});

	expect(response.ok()).toBeTruthy();

	const dp = new DashboardPage(page);
	await dp.goto();

	const pageOverflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
	expect(pageOverflow).toBeLessThanOrEqual(1);

	for (const testId of ['expense-chart-scroll', 'net-worth-chart-scroll']) {
		const chartScroll = page.locator(`[data-testid="${testId}"]`);
		const hasInternalScroll = await chartScroll.evaluate(
			(el) => el.scrollWidth > el.clientWidth
		);
		expect(hasInternalScroll).toBeTruthy();

		const dimensions = await chartScroll.evaluate((el) => {
			const card = el.closest('.cc-chart-card');
			return {
				scrollRight: el.getBoundingClientRect().right,
				cardRight: card?.getBoundingClientRect().right ?? 0,
			};
		});
		expect(dimensions.scrollRight).toBeLessThanOrEqual(dimensions.cardRight + 1);
	}
});
