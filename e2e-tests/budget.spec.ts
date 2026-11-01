import type { APIRequestContext } from '@playwright/test';
import { test, expect } from './fixtures';
import { BudgetPage } from './pages/budget.page';
import { TransactionsPage } from './pages/transactions.page';

async function addTransaction(request: APIRequestContext, options: {
	label: string; amount: string; date?: string; category?: string; account?: string; mode?: string;
}) {
	const response = await request.post('/transactions', { form: {
		date: options.date ?? '2024-02-15', label: options.label, amount: options.amount,
		amount_mode: options.mode ?? 'debit', category_id: options.category ?? '1', account_id: options.account ?? '3',
	} });
	expect(response.ok()).toBeTruthy();
}

test('monthly budget totals expenses and credits by category', async ({ page, request }) => {
	await addTransaction(request, { label: 'February food', amount: '100.00' });
	await addTransaction(request, { label: 'Food refund', amount: '20.00', mode: 'credit' });
	await addTransaction(request, { label: 'Unsorted expense', amount: '25.00', category: '0' });
	await addTransaction(request, { label: 'January food', amount: '50.00', date: '2024-01-31' });
	await addTransaction(request, { label: 'March food', amount: '999.00', date: '2024-03-01' });
	await addTransaction(request, { label: 'Asset change', amount: '500.00', account: '1' });
	const budget = new BudgetPage(page);
	await budget.goto();

	await expect(page.getByTestId('budget-month-label')).toHaveText('February 2024');
	await expect(budget.getTotal('spending')).toHaveText('$125.00');
	await expect(budget.getTotal('credits')).toHaveText('$20.00');
	await expect(budget.getTotal('net')).toHaveText('$105.00');
	await expect(budget.getCategory('1').getByTestId('budget-category-net')).toHaveText('$80.00');
	await expect(budget.getCategory('1').getByTestId('budget-category-change')).toHaveText('+$30.00');
	await expect(budget.getCategory('1')).toContainText('80.0%');
	await expect(budget.getCategory('0').getByTestId('budget-category-net')).toHaveText('$25.00');
	await expect(budget.getCategory('2').getByTestId('budget-category-net')).toHaveText('$0.00');
	await expect(page.getByTestId('budget-month-change')).toContainText('+$55.00');
});

test('month selection survives reload and supports empty months', async ({ page }) => {
	const budget = new BudgetPage(page);
	await budget.goto();
	await budget.selectMonth('2024-12');
	await expect(page).toHaveURL(/month=2024-12/);
	await expect(budget.getMonth()).toHaveValue('2024-12');
	await expect(page.getByTestId('budget-empty')).toBeVisible();
	await expect(budget.getTotal('net')).toHaveText('$0.00');
	await page.reload();
	await expect(budget.getMonth()).toHaveValue('2024-12');
	await page.getByRole('link', { name: 'Next month', exact: true }).click();
	await expect(budget.getMonth()).toHaveValue('2025-01');
	await page.getByRole('link', { name: 'Previous month', exact: true }).click();
	await expect(budget.getMonth()).toHaveValue('2024-12');
});

test('category drilldown preserves month and refreshes totals after edits and deletion', async ({ page, request }) => {
	await addTransaction(request, { label: 'Drilldown food', amount: '100.00' });
	await addTransaction(request, { label: 'Other category', amount: '50.00', category: '2' });
	const budget = new BudgetPage(page);
	const transactions = new TransactionsPage(page);
	await budget.goto();
	await budget.getCategory('1').getByRole('link', { name: 'Groceries', exact: true }).click();
	await expect(page).toHaveURL(/category_id=1/);
	await expect(transactions.getRows()).toHaveCount(1);
	await expect(transactions.getBreakdownTotal('net')).toHaveText('$100.00');
	await expect(transactions.getDateFrom()).toHaveValue('2024-02-01');
	await expect(transactions.getDateTo()).toHaveValue('2024-02-29');

	await transactions.clickEditOnRow(transactions.getRows().first());
	await transactions.getEditRows().first().locator('input[name="amount"]').fill('40.00');
	await transactions.saveEditRow(transactions.getEditRows().first());
	await expect(transactions.getBreakdownTotal('net')).toHaveText('$40.00');
	await expect(transactions.getRows()).toHaveCount(1);
	await expect(transactions.getDateFrom()).toHaveValue('2024-02-01');

	page.once('dialog', dialog => dialog.accept());
	await transactions.clickDeleteOnRow(transactions.getRows().first());
	await expect(transactions.getRows()).toHaveCount(0);
	await expect(transactions.getBreakdownTotal('net')).toHaveText('$0.00');
	await budget.goto();
	await expect(budget.getCategory('1').getByTestId('budget-category-net')).toHaveText('$0.00');
});

test('uncategorized drilldown selects only uncategorized expenses', async ({ page, request }) => {
	await addTransaction(request, { label: 'Uncategorized purchase', amount: '12.34', category: '0' });
	await addTransaction(request, { label: 'Categorized purchase', amount: '99.00' });
	const budget = new BudgetPage(page);
	const transactions = new TransactionsPage(page);
	await budget.goto();
	await budget.getCategory('0').getByRole('link', { name: 'Uncategorized' }).click();
	await expect(transactions.getRows()).toHaveCount(1);
	await expect(transactions.getRows().first()).toContainText('Uncategorized purchase');
	await expect(transactions.getBreakdownTotal('net')).toHaveText('$12.34');
	await page.reload();
	await expect(transactions.getRows()).toHaveCount(1);
});

test('budget shows negative net expenses when credits exceed spending', async ({ page, request }) => {
	await addTransaction(request, { label: 'Credit only', amount: '30.00', mode: 'credit' });
	const budget = new BudgetPage(page);
	await budget.goto();
	await expect(budget.getTotal('net')).toHaveText('-$30.00');
	await expect(budget.getCategory('1').getByTestId('budget-category-net')).toHaveText('-$30.00');
	await expect(budget.getCategory('1')).toContainText('0.0%');
});

test('budget rejects invalid month values', async ({ request }) => {
	for (const month of ['2024-13', 'not-a-month', '2024-2', '0000-01']) {
		const response = await request.get(`/budget?month=${month}`);
		expect(response.status()).toBe(400);
	}
});

test('category contributions inherit with over-budget and zero-contribution states', async ({ page, request }) => {
	await addTransaction(request, { label: 'Budgeted food', amount: '100.00' });
	await addTransaction(request, { label: 'Food credit', amount: '20.00', mode: 'credit' });
	await addTransaction(request, { label: 'Unbudgeted utility', amount: '50.00', category: '2' });
	const budget = new BudgetPage(page);
	await budget.goto();
	await budget.getLimitInput('1').fill('75.00');
	await budget.getLimitInput('2').fill('0');
	await budget.getLimitInput('0').fill('25.00');
	await budget.saveLimits();
	await expect(budget.getLimitCard('1').getByTestId('budget-limit-status')).toHaveText('Over by $5.00');
	await expect(budget.getLimitCard('2').getByTestId('budget-limit-status')).toHaveText('Over by $50.00');
	await expect(budget.getLimitCard('0').getByTestId('budget-limit-status')).toHaveText('$25.00 remaining');
	await expect(page.getByTestId('budget-total-limits')).toHaveText('Monthly contributions: $100.00');
	await page.reload();
	await expect(budget.getLimitInput('1')).toHaveValue('75.00');
	await expect(budget.getLimitInput('2')).toHaveValue('0.00');

	await budget.selectMonth('2024-03');
	await expect(budget.getLimitInput('1')).toHaveValue('75.00');
	await expect(budget.getLimitCard('1').getByTestId('budget-rollover')).toHaveText('-$5.00');
	await budget.getLimitInput('1').fill('150.00');
	await budget.saveLimits();
	await budget.goto('2024-02');
	await expect(budget.getLimitInput('1')).toHaveValue('75.00');
	await budget.getLimitInput('1').fill('');
	await budget.saveLimits();
	await expect(budget.getLimitCard('1').getByTestId('budget-limit-status')).toHaveText('No limit set');
	await expect(budget.getLimitInput('2')).toHaveValue('0.00');
});

test('limit validation rejects invalid amounts without changing saved limits', async ({ request }) => {
	const initial = await request.post('/budget/limits', { form: { month: '2024-02', limit_1: '10' } });
	expect(initial.ok()).toBeTruthy();
	for (const value of ['-1', 'bad', 'NaN', 'Infinity', '1.001']) {
		const response = await request.post('/budget/limits', { form: { month: '2024-02', limit_1: '20', limit_2: value } });
		expect(response.status()).toBe(400);
	}
	const payload = await (await request.get('/settings/export/backup')).json();
	expect(payload.monthly_budgets).toHaveLength(1);
	expect(payload.monthly_budgets[0].amount_cents).toBe(1000);
});

test('recurring travel budget accumulates rollover and derives annual progress', async ({ page, request }) => {
	await request.post('/budget/limits', { form: { month: '2024-01', limit_1: '200' } });
	await request.post('/budget/limits', { form: { month: '2024-07', limit_1: '300' } });
	await addTransaction(request, { label: 'Trip', amount: '500', date: '2024-03-15' });
	const budget = new BudgetPage(page);
	await budget.goto('2024-03');
	await expect(budget.getLimitInput('1')).toHaveValue('200.00');
	await expect(budget.getBudgetMetric('1', 'rollover')).toHaveText('$400.00');
	await expect(budget.getBudgetMetric('1', 'available')).toHaveText('$600.00');
	await expect(budget.getLimitCard('1').getByTestId('budget-limit-status')).toHaveText('$100.00 remaining');
	await expect(budget.getBudgetMetric('1', 'annual-spending')).toHaveText('$500.00 of $3,000.00');
	await expect(budget.getBudgetMetric('1', 'next-change')).toContainText('July 2024 · $300.00/month');
	await expect(page.getByTestId('budget-annual-summary')).toContainText('January–March 2024');
	await budget.selectMonth('2024-04');
	await expect(budget.getBudgetMetric('1', 'rollover')).toHaveText('$100.00');
	await expect(budget.getBudgetMetric('1', 'available')).toHaveText('$300.00');
	await budget.selectMonth('2025-01');
	await expect(budget.getLimitInput('1')).toHaveValue('300.00');
	await expect(budget.getBudgetMetric('1', 'rollover')).toHaveText('$0.00');
	await expect(budget.getBudgetMetric('1', 'available')).toHaveText('$300.00');
	await expect(budget.getBudgetMetric('1', 'annual-spending')).toHaveText('$0.00 of $3,600.00');
});

test('editing one inherited contribution submits only changes and preserves scheduled changes', async ({ page, request }) => {
	await request.post('/budget/limits', { form: { month: '2024-01', limit_1: '200', limit_2: '50' } });
	await request.post('/budget/limits', { form: { month: '2024-07', limit_1: '300' } });
	const budget = new BudgetPage(page);
	await budget.goto('2024-03');
	await budget.getLimitInput('2').fill('75');
	const submission = page.waitForRequest(req => req.method() === 'POST' && req.url().endsWith('/budget/limits'));
	await budget.saveLimits();
	const submitted = await submission;
	const fields = await new Response(submitted.postData(), {
		headers: { 'Content-Type': submitted.headers()['content-type'] },
	}).formData();
	expect([...fields.keys()]).toEqual(['month', 'limit_2']);
	let payload = await (await request.get('/settings/export/backup')).json();
	expect(payload.monthly_budgets.filter((row: {month: string}) => row.month === '2024-03')).toHaveLength(1);
	await budget.saveLimits();
	payload = await (await request.get('/settings/export/backup')).json();
	expect(payload.monthly_budgets).toHaveLength(4);
	await budget.getLimitInput('1').fill('250');
	await budget.saveLimits();
	await budget.selectMonth('2024-06');
	await expect(budget.getLimitInput('1')).toHaveValue('250.00');
	await budget.selectMonth('2024-07');
	await expect(budget.getLimitInput('1')).toHaveValue('300.00');
});

test('deficits carry, zero preserves rollover, and stop records survive backup restore', async ({ page, request }) => {
	await request.post('/budget/limits', { form: { month: '2024-01', limit_1: '100', limit_0: '10' } });
	await addTransaction(request, { label: 'Overspend', amount: '250', date: '2024-01-15' });
	const budget = new BudgetPage(page);
	await budget.goto('2024-02');
	await expect(budget.getBudgetMetric('1', 'rollover')).toHaveText('-$150.00');
	await expect(budget.getBudgetMetric('1', 'available')).toHaveText('-$50.00');
	await expect(budget.getLimitCard('1').getByTestId('budget-limit-status')).toHaveText('Over by $50.00');
	await budget.getLimitInput('0').fill('0');
	await budget.saveLimits();
	await expect(budget.getBudgetMetric('0', 'available')).toHaveText('$10.00');
	await budget.getLimitInput('1').fill('');
	await budget.getLimitInput('0').fill('');
	await budget.saveLimits();
	await expect(budget.getLimitCard('1').getByTestId('budget-limit-status')).toHaveText('No limit set');
	const payload = await (await request.get('/settings/export/backup')).json();
	expect(payload.version).toBe(4);
	expect(payload.monthly_budgets.filter((row: {amount_cents: number | null}) => row.amount_cents === null)).toHaveLength(2);
	await request.post('/dev/reset');
	const restored = await request.post('/settings/import/backup', { multipart: {
		file: { name: 'recurring-backup.json', mimeType: 'application/json', buffer: Buffer.from(JSON.stringify(payload)) },
	} });
	expect(restored.ok()).toBeTruthy();
	await budget.goto('2024-03');
	await expect(budget.getLimitInput('1')).toHaveValue('');
	await budget.getLimitInput('1').fill('100');
	await budget.saveLimits();
	await expect(budget.getBudgetMetric('1', 'rollover')).toHaveText('$0.00');
	await expect(budget.getBudgetMetric('1', 'available')).toHaveText('$100.00');
	await expect(budget.getBudgetMetric('1', 'annual-spending')).toHaveText('$250.00 of $1,100.00');
});

test('backup restore preserves monthly limits including uncategorized limits', async ({ page, request }) => {
	await request.post('/budget/limits', { form: { month: '2024-02', limit_1: '42.29', limit_0: '0' } });
	const payload = await (await request.get('/settings/export/backup')).json();
	await request.post('/dev/reset');
	const restored = await request.post('/settings/import/backup', { multipart: {
		file: { name: 'budget-backup.json', mimeType: 'application/json', buffer: Buffer.from(JSON.stringify(payload)) },
	} });
	expect(restored.ok()).toBeTruthy();
	const budget = new BudgetPage(page);
	await budget.goto();
	await expect(budget.getLimitInput('1')).toHaveValue('42.29');
	await expect(budget.getLimitInput('0')).toHaveValue('0.00');
});

test('transaction breakdown follows multiple categories, search, creation, and date presets', async ({ page, request }) => {
	await addTransaction(request, { label: 'Breakdown grocery', amount: '10.00' });
	await addTransaction(request, { label: 'Breakdown utility', amount: '50.00', category: '2' });
	await addTransaction(request, { label: 'Breakdown transport', amount: '99.00', category: '3' });
	const transactions = new TransactionsPage(page);
	await page.goto('/transactions?date_preset=custom&date_from=2024-02-01&date_to=2024-02-29&category_id=1&category_id=2');
	await expect(transactions.getBreakdown()).toHaveJSProperty('open', false);
	await expect(transactions.getBreakdownRows().first()).not.toBeVisible();
	await expect(transactions.getBreakdownTotal('net')).toBeVisible();
	await transactions.getBreakdownToggle().focus();
	await transactions.getBreakdownToggle().press('Enter');
	await expect(transactions.getBreakdown()).toHaveJSProperty('open', true);
	await expect(transactions.getBreakdownRows().first()).toBeVisible();
	await expect(transactions.getRows()).toHaveCount(2);
	await expect(transactions.getBreakdownRows()).toHaveCount(2);
	await expect(transactions.getBreakdownTotal('net')).toHaveText('$60.00');
	await page.reload();
	await expect(transactions.getRows()).toHaveCount(2);
	await transactions.getLabelSearch().fill('Breakdown grocery');
	await expect(transactions.getRows()).toHaveCount(1);
	await expect(transactions.getBreakdownTotal('net')).toHaveText('$10.00');
	await expect(transactions.getBreakdown()).toHaveJSProperty('open', true);

	await transactions.fillCreateForm({ date: '2024-02-20', label: 'Breakdown grocery extra', amount: '5.00', categoryId: '1' });
	await transactions.submitCreate();
	await expect(transactions.getRows()).toHaveCount(2);
	await expect(transactions.getBreakdownTotal('net')).toHaveText('$15.00');
	await expect(transactions.getLabelSearch()).toHaveValue('Breakdown grocery');
	await expect(transactions.getDateTo()).toHaveValue('2024-02-29');
	await transactions.getPresetButton('all_time').click();
	await expect(transactions.getPresetButton('all_time')).toHaveClass(/btn-primary/);
	await expect(transactions.getDateFrom()).toHaveValue('');
	await transactions.getLabelSearch().fill('Breakdown');
	await expect(transactions.getRows()).toHaveCount(3);
	await expect(transactions.getBreakdownTotal('net')).toHaveText('$65.00');
	await expect(page).toHaveURL(/date_preset=all_time/);
	await transactions.getBreakdownToggle().click();
	await expect(transactions.getBreakdown()).toHaveJSProperty('open', false);
	await page.reload();
	await expect(transactions.getBreakdown()).toHaveJSProperty('open', false);
	await expect(transactions.getBreakdownTotal('net')).toBeVisible();
	await expect(transactions.getRows()).toHaveCount(3);
});

test('net worth category breakdown shows inflows and outflows with signed net change', async ({ page, request }) => {
	await addTransaction(request, { label: 'Asset debit', amount: '100.00', account: '1' });
	await addTransaction(request, { label: 'Asset credit', amount: '250.00', account: '1', mode: 'credit' });
	await addTransaction(request, { label: 'Expense debit', amount: '999.00' });
	const transactions = new TransactionsPage(page);
	await page.goto('/transactions?account_type=net_worth&date_preset=custom&date_from=2024-02-01&date_to=2024-02-29');
	await expect(transactions.getBreakdown()).toContainText('Inflows');
	await expect(transactions.getBreakdownTotal('spending')).toHaveText('$100.00');
	await expect(transactions.getBreakdownTotal('credits')).toHaveText('$250.00');
	await expect(transactions.getBreakdownTotal('net')).toHaveText('$150.00');
});
