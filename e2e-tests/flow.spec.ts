import { test, expect } from './fixtures';
import { FlowPage } from './pages/flow.page';

async function seededIds(request: any) {
	const backup = await (await request.get('/settings/export/backup')).json();
	return {
		expenseAccountId: backup.accounts.find((account: any) => account.label === 'Daily Expenses').legacy_numeric_id,
		netWorthAccountId: backup.accounts.find((account: any) => account.label === 'Checking').legacy_numeric_id,
		groceriesId: backup.categories.find((category: any) => category.label === 'Groceries').legacy_numeric_id,
		utilitiesId: backup.categories.find((category: any) => category.label === 'Utilities').legacy_numeric_id,
	};
}

async function addNetWorthChange(request: any, accountId: number, date: string, amount: string, mode = 'credit') {
	const response = await request.post('/transactions?account_type=net_worth', {
		form: {
			date,
			label: `Flow net worth ${amount}`,
			amount,
			amount_mode: mode,
			account_id: String(accountId),
			category_id: '0',
			account_type: 'net_worth',
		},
	});
	expect(response.ok()).toBeTruthy();
}

async function addIncome(request: any, year: number, gross: string, federal: string, state: string) {
	const response = await request.post('/income', {
		form: {
			tax_year: String(year),
			gross_income: gross,
			federal_tax: federal,
			state_tax: state,
		},
	});
	expect(response.ok()).toBeTruthy();
}

async function addExpense(request: any, accountId: number, categoryId: number, date: string, amount: string, mode = 'debit') {
	const response = await request.post('/transactions?account_type=expenses', {
		form: {
			date,
			label: `Flow ${categoryId} ${amount}`,
			amount,
			amount_mode: mode,
			account_id: String(accountId),
			category_id: String(categoryId),
			account_type: 'expenses',
		},
	});
	expect(response.ok()).toBeTruthy();
}

test('flow renders annual taxes, expense categories, leftover, and interactive paths', async ({ page, request }) => {
	const ids = await seededIds(request);
	await addIncome(request, 2024, '100000.00', '18000.00', '7000.00');
	await addExpense(request, ids.expenseAccountId, ids.groceriesId, '2024-04-10', '1000.00');
	await addExpense(request, ids.expenseAccountId, ids.utilitiesId, '2024-05-10', '500.00');
	await addNetWorthChange(request, ids.netWorthAccountId, '2024-12-31', '73500.00');

	const flow = new FlowPage(page);
	await flow.goto(2024);

	await expect(page.locator('h1')).toContainText('Flow');
	await expect(flow.getSummary()).toContainText('$100,000.00');
	await expect(flow.getSummary()).toContainText('$25,000.00');
	await expect(flow.getSummary()).toContainText('$1,500.00');
	await expect(flow.getSummary()).toContainText('$73,500.00');
	await expect(flow.getDetails()).toContainText('Groceries');
	await expect(flow.getDetails()).toContainText('Utilities');

	await expect(flow.getSankey()).toBeVisible();
	await expect(flow.getNode('gross')).toBeVisible();
	await expect(flow.getNode('left-over')).toBeVisible();
	await expect(flow.getGroup('taxes')).toHaveText('Taxes');
	await expect(flow.getGroup('expenses')).toHaveText('Expenses');
	await expect(flow.getGroup('left-over')).toHaveText('Left Over');

	const federalTaxBox = await flow.getNode('federal-tax').locator('rect').boundingBox();
	const stateTaxBox = await flow.getNode('state-tax').locator('rect').boundingBox();
	const expenseBoxes = await page.locator('[data-flow-node-kind="expense"] rect').evaluateAll((rects) =>
		rects.map((rect) => rect.getBoundingClientRect().top),
	);
	expect(federalTaxBox).not.toBeNull();
	expect(stateTaxBox).not.toBeNull();
	expect(expenseBoxes.length).toBeGreaterThan(0);
	expect(federalTaxBox!.y).toBeLessThan(Math.min(...expenseBoxes));
	expect(stateTaxBox!.y).toBeLessThan(Math.min(...expenseBoxes));

	await expect(flow.getNetWorthComparison()).toContainText('Left Over');
	await expect(flow.getNetWorthComparison()).toContainText('$73,500.00');
	await expect(flow.getNetWorthComparison()).toContainText('+$73,500.00');
	await expect(flow.getComparisonMessage()).toHaveText('Net worth change matched the recorded left over.');
	await flow.getNode('left-over').focus();
	await expect(flow.getTooltip()).toBeVisible();
	await expect(flow.getTooltip()).toContainText('$73,500.00');

	const layout = await page.evaluate(() => {
		const scroller = document.querySelector('.cc-flow-scroll') as HTMLElement;
		return {
			pageOverflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
			scrollerClientWidth: scroller.clientWidth,
			scrollerScrollWidth: scroller.scrollWidth,
			viewportWidth: window.innerWidth,
		};
	});
	expect(layout.pageOverflow).toBeLessThanOrEqual(1);
	if (layout.viewportWidth < 760) {
		expect(layout.scrollerScrollWidth).toBeGreaterThan(layout.scrollerClientWidth);
	}

	await page.locator('[data-flow-node-kind="expense"]').filter({ hasText: 'Groceries' }).click();
	await expect(page).toHaveURL(/\/transactions\?/);
	await expect(page).toHaveURL(/category_id=1/);
	await expect(page).toHaveURL(/date_from=2024-01-01/);
});

test('flow exposes a balanced shortfall and switches between years', async ({ page, request }) => {
	const ids = await seededIds(request);
	await addIncome(request, 2022, '1000.00', '100.00', '0');
	await addIncome(request, 2023, '2000.00', '200.00', '0');
	await addExpense(request, ids.expenseAccountId, ids.groceriesId, '2022-03-01', '1500.00');
	await addNetWorthChange(request, ids.netWorthAccountId, '2022-12-31', '600.00', 'debit');
	await addNetWorthChange(request, ids.netWorthAccountId, '2023-12-31', '2000.00');

	const flow = new FlowPage(page);
	await flow.goto(2022);
	await expect(flow.getSummary()).toContainText('Savings / Debt Used');
	await expect(flow.getSummary()).toContainText('$600.00');
	await expect(flow.getNode('shortfall')).toBeVisible();
	await expect(flow.getNode('left-over')).toHaveCount(0);
	await expect(flow.getGroup('funding-gap')).toHaveText('Funding Gap');
	await expect(flow.getNetWorthComparison()).toContainText('Cash-flow Shortfall');
	await expect(flow.getComparisonMessage()).toHaveText('Net worth change matched the cash-flow result.');

	await flow.getYearSelect().selectOption('2023');
	await expect(page).toHaveURL(/year=2023/);
	await expect(flow.getSummary()).toContainText('$1,800.00');
	await expect(flow.getNode('left-over')).toBeVisible();
	await expect(flow.getNetWorthComparison()).toContainText('+$2,000.00');
	await expect(flow.getComparisonMessage()).toHaveText('Net worth change was $200.00 more than the recorded left over.');
});

test('flow links to income when the selected year has expenses but no summary', async ({ page }) => {
	const flow = new FlowPage(page);
	await flow.goto(2026);
	await expect(flow.getEmptyIncome()).toBeVisible();
	await expect(flow.getEmptyIncome().locator('a[href="/income"]')).toBeVisible();
});

test('flow includes uncategorized spending and net expense credits', async ({ page, request }) => {
	const ids = await seededIds(request);
	await addIncome(request, 2021, '1000.00', '0', '0');
	await addExpense(request, ids.expenseAccountId, 0, '2021-03-01', '200.00');
	await addExpense(request, ids.expenseAccountId, ids.utilitiesId, '2021-03-02', '50.00', 'credit');

	const flow = new FlowPage(page);
	await flow.goto(2021);
	await expect(flow.getSummary()).toContainText('$150.00');
	await expect(flow.getSummary()).toContainText('$850.00');
	await expect(flow.getDetails()).toContainText('Uncategorized');
	await expect(flow.getDetails()).toContainText('Expense refunds / credits');
	await expect(flow.getNode('refunds')).toBeVisible();
	await expect(flow.getNetWorthComparison()).toContainText('Not available');
	await expect(flow.getComparisonMessage()).toHaveText('No net-worth activity was recorded for this year.');
});
