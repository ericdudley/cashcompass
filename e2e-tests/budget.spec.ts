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

async function saveBudget(request: APIRequestContext, category: string, month: string, period: 'monthly' | 'annual', amount: string, rollover = false) {
	const response = await request.post(`/budget/categories/${category}`, { form: {
		month, year: month.slice(0, 4), period, amount, rollover: String(rollover),
	} });
	expect(response.ok(), await response.text()).toBeTruthy();
}

test('compact monthly cards edit contributions, reset by default, and preserve later changes', async ({ page, request }) => {
	await addTransaction(request, { label: 'Budgeted food', amount: '100.00' });
	await addTransaction(request, { label: 'Food credit', amount: '20.00', mode: 'credit' });
	await addTransaction(request, { label: 'Utility', amount: '50.00', category: '2' });
	const budget = new BudgetPage(page);
	await budget.goto();
	await expect(budget.getAmount()).toHaveCount(0);
	await budget.edit('1', '75');
	await budget.edit('2', '0');
	await budget.edit('0', '25');
	await expect(budget.getStatus('1')).toHaveText('Over by $5.00');
	await expect(budget.getLimitCard('1').getByTestId('budget-bar-labels')).toContainText('Spent $80.00');
	await expect(budget.getStatus('2')).toHaveText('Over by $50.00');
	await expect(budget.getStatus('0')).toHaveText('$25.00 remaining');
	await expect(budget.getBar('1')).toHaveAccessibleName(/Over by \$5.00/);
	await expect(budget.getLimitCard('1').getByTestId('budget-pace-marker')).toHaveCount(0);
	await budget.selectMonth('2024-03');
	await expect(budget.getStatus('1')).toHaveText('$75.00 remaining');
	await budget.edit('1', '150');
	await budget.goto('2024-02');
	await budget.edit('1', '');
	await expect(budget.getStatus('1')).toHaveText('No budget set');
	await budget.selectMonth('2024-03');
	await expect(budget.getStatus('1')).toHaveText('$150.00 remaining');
});

test('monthly rollover bar consumes the allowance then reserve and annualizes only in annual view', async ({ page, request }) => {
	await saveBudget(request, '1', '2024-01', 'monthly', '200', true);
	await saveBudget(request, '1', '2024-07', 'monthly', '300', true);
	await addTransaction(request, { label: 'Trip', amount: '500', date: '2024-03-15' });
	const budget = new BudgetPage(page);
	await budget.goto('2024-03');
	await expect(budget.getStatus('1')).toHaveText('$100.00 remaining');
	await expect(budget.getLimitCard('1').getByTestId('budget-bar-labels')).toContainText('Spent $500.00');
	await expect(budget.getLimitCard('1').getByTestId('budget-bar-labels')).toContainText('Rollover left $100.00');
	await expect(budget.getBar('1').getByTestId('budget-segment-monthly')).toHaveCount(0);
	await expect(budget.getLimitCard('1').getByTestId('budget-using-rollover')).toBeVisible();
	await budget.openDetails('1');
	await expect(budget.getLimitCard('1')).toContainText('Rollover into this month$400.00');
	await expect(budget.getLimitCard('1').getByTestId('budget-next-change')).toContainText('2024-07 · $300.00/month');
	await budget.gotoAnnual();
	await expect(budget.getLimitCard('1')).toHaveAttribute('data-representation', 'annual');
	await expect(budget.getStatus('1')).toHaveText('$2,500.00 remaining');
	await expect(budget.getLimitCard('1').getByTestId('budget-allowance')).toHaveText('$3,000.00 annual budget');
	await expect(budget.getLimitCard('1').getByTestId('budget-pace-marker')).toBeVisible();
	await budget.goto('2025-01');
	await expect(budget.getStatus('1')).toHaveText('$300.00 remaining');
});

test('per-category edits skip unchanged records and keep scheduled changes independent', async ({ page, request }) => {
	await request.post('/budget/limits', { form: { month: '2024-01', limit_1: '200', limit_2: '50' } });
	await request.post('/budget/limits', { form: { month: '2024-07', limit_1: '300' } });
	const budget = new BudgetPage(page);
	await budget.goto('2024-03');
	await budget.edit('2', '75');
	let payload = await (await request.get('/settings/export/backup')).json();
	expect(payload.monthly_budgets.filter((row: {month: string}) => row.month === '2024-03')).toHaveLength(1);
	await budget.edit('2', '75');
	payload = await (await request.get('/settings/export/backup')).json();
	expect(payload.monthly_budgets).toHaveLength(4);
	expect(payload.monthly_budget_rollover).toEqual([]);
	await budget.edit('1', '250', { rollover: true });
	await budget.selectMonth('2024-07');
	await expect(budget.getLimitCard('1').getByTestId('budget-allowance')).toContainText('$300.00 this month');
	await budget.openDetails('1');
	await expect(budget.getLimitCard('1')).toContainText('Rollover on');
});

test('deficits, zero contributions and stopped budgets survive v5 restore', async ({ page, request }) => {
	await saveBudget(request, '1', '2024-01', 'monthly', '100', true);
	await saveBudget(request, '0', '2024-01', 'monthly', '10', true);
	await saveBudget(request, '2', '2024-01', 'annual', '3000');
	await addTransaction(request, { label: 'Overspend', amount: '250', date: '2024-01-15' });
	const budget = new BudgetPage(page);
	await budget.goto('2024-02');
	await expect(budget.getStatus('1')).toHaveText('Over by $50.00');
	await expect(budget.getLimitCard('1')).toContainText('$150.00 carried overspend');
	await budget.edit('0', '0', { rollover: true });
	await expect(budget.getStatus('0')).toHaveText('$10.00 remaining');
	await budget.edit('1', '', { rollover: true });
	await budget.edit('0', '', { rollover: true });
	const payload = await (await request.get('/settings/export/backup')).json();
	expect(payload.version).toBe(5);
	expect(payload.monthly_budgets.filter((row: {amount_cents: number | null}) => row.amount_cents === null)).toHaveLength(2);
	await request.post('/dev/reset');
	const restored = await request.post('/settings/import/backup', { multipart: {
		file: { name: 'budget-v5.json', mimeType: 'application/json', buffer: Buffer.from(JSON.stringify(payload)) },
	} });
	expect(restored.ok()).toBeTruthy();
	await budget.goto('2024-03');
	await expect(budget.getStatus('1')).toHaveText('No budget set');
	await expect(budget.getLimitCard('2')).toHaveAttribute('data-period', 'annual');
	await budget.edit('1', '100', { rollover: true });
	await expect(budget.getStatus('1')).toHaveText('$100.00 remaining');
});

test('annual budgets show a neutral pace marker and year-scoped edits without a monthly limit', async ({ page, request }) => {
	await saveBudget(request, '1', '2024-01', 'monthly', '500');
	await saveBudget(request, '2', '2024-01', 'annual', '3000');
	await addTransaction(request, { label: 'Annual travel', amount: '1000', date: '2024-01-15', category: '2' });
	const budget = new BudgetPage(page);
	await budget.goto('2024-01');
	await expect(page.getByTestId('budget-monthly-group').getByTestId('budget-limit-card').filter({ hasText: 'Groceries' })).toBeVisible();
	await expect(page.getByTestId('budget-annual-group').getByTestId('budget-limit-card')).toHaveCount(1);
	await expect(budget.getLimitCard('2')).toHaveAttribute('data-representation', 'annual');
	await expect(budget.getStatus('2')).toHaveText('$2,000.00 remaining');
	await expect(budget.getStatus('2')).not.toHaveClass(/text-error/);
	await expect(budget.getLimitCard('2').getByTestId('budget-pace-label')).toContainText('8% of year');
	await expect(budget.getLimitCard('2').getByTestId('budget-allowance')).toHaveText('$3,000.00 annual budget');
	await budget.edit('2', '4000');
	await expect(budget.getStatus('2')).toHaveText('$3,000.00 remaining');
	await budget.goto('2025-01');
	await expect(budget.getLimitCard('2').getByTestId('budget-allowance')).toHaveText('$4,000.00 annual budget');
	const rejected = await request.post('/budget/limits', { form: { month: '2024-01', limit_1: '25', limit_2: '10' } });
	expect(rejected.status()).toBe(400);
	await budget.gotoAnnual();
	await expect(budget.getLimitCard('1')).toHaveAttribute('data-representation', 'annual');
	await expect(budget.getLimitCard('1').getByTestId('budget-allowance')).toHaveText('$6,000.00 annual budget');
});

test('type conversion requires a new amount, preserves history and starts monthly amounts in January', async ({ page, request }) => {
	await saveBudget(request, '1', '2023-01', 'monthly', '100');
	await saveBudget(request, '1', '2024-07', 'monthly', '300');
	const budget = new BudgetPage(page);
	await budget.goto('2024-05');
	await budget.openEdit('1');
	await page.getByLabel('Budget type', { exact: true }).selectOption('annual');
	await expect(budget.getAmount()).toHaveValue('');
	await expect(budget.getAmount()).toHaveAttribute('required', '');
	await expect(page.getByLabel('Effective month', { exact: true })).not.toBeVisible();
	await budget.getAmount().fill('2400');
	await budget.saveBudget();
	await budget.goto('2023-12');
	await expect(budget.getLimitCard('1')).toHaveAttribute('data-period', 'monthly');
	await budget.goto('2024-01');
	await expect(budget.getLimitCard('1')).toHaveAttribute('data-period', 'annual');
	await budget.edit('1', '150', { period: 'monthly', rollover: false });
	await expect(budget.getLimitCard('1').getByTestId('budget-allowance')).toHaveText('$150.00 this month');
	await budget.selectMonth('2024-07');
	await expect(budget.getLimitCard('1').getByTestId('budget-allowance')).toHaveText('$300.00 this month');
});

test('future budgets show plans without progress or pace and reject invalid edits atomically', async ({ page, request }) => {
	await saveBudget(request, '1', '9999-01', 'monthly', '100');
	await saveBudget(request, '2', '9999-01', 'annual', '2000');
	const budget = new BudgetPage(page);
	await budget.goto('9999-02');
	await expect(budget.getStatus('1')).toHaveText('Planned $100.00');
	await expect(budget.getBar('1')).toHaveCount(0);
	await expect(budget.getStatus('2')).toHaveText('Planned $2,000.00');
	await expect(budget.getLimitCard('2').getByTestId('budget-pace-marker')).toHaveCount(0);
	const before = await (await request.get('/settings/export/backup')).json();
	for (const fields of [{ period: 'weekly', amount: '10' }, { period: 'annual', amount: '' }, { period: 'monthly', amount: '-1' }, { period: 'monthly', amount: '50', rollover: 'yes' }]) {
		const response = await request.post('/budget/categories/1', { form: { month: '9999-02', rollover: 'false', ...fields } });
		expect(response.status()).toBe(400);
	}
	const after = await (await request.get('/settings/export/backup')).json();
	expect(after.monthly_budgets).toEqual(before.monthly_budgets);
	expect(after.budget_plans).toEqual(before.budget_plans);
});

test('limit validation rejects invalid amounts without changing saved limits', async ({ request }) => {
	await request.post('/budget/limits', { form: { month: '2024-02', limit_1: '10' } });
	for (const value of ['-1', 'bad', 'NaN', 'Infinity', '1.001']) {
		const response = await request.post('/budget/limits', { form: { month: '2024-02', limit_1: '20', limit_2: value } });
		expect(response.status()).toBe(400);
	}
	const payload = await (await request.get('/settings/export/backup')).json();
	expect(payload.monthly_budgets).toHaveLength(1);
	expect(payload.monthly_budgets[0].amount_cents).toBe(1000);
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
