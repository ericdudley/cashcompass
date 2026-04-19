import { test, expect } from './fixtures';
import { TransactionsPage } from './pages/transactions.page';

// Current month date for creating transactions that appear in the default "this_month" filter.
function currentMonthDate(day = 15): string {
	const now = new Date();
	const year = now.getFullYear();
	const month = String(now.getMonth() + 1).padStart(2, '0');
	return `${year}-${month}-${String(day).padStart(2, '0')}`;
}

test('transactions page loads', async ({ page }) => {
	const tp = new TransactionsPage(page);
	await tp.goto();
	await expect(tp.getList()).toBeVisible();
});

test('seeded transactions appear', async ({ page }) => {
	const tp = new TransactionsPage(page);
	await tp.goto();
	await expect(tp.getRows().first()).toBeVisible();
});

test('default filter is this month', async ({ page }) => {
	const tp = new TransactionsPage(page);
	await tp.goto();
	await expect(tp.getPresetButton('this_month')).toHaveClass(/bg-emerald-600/);
});

test('create form is visible', async ({ page }) => {
	const tp = new TransactionsPage(page);
	await tp.goto();
	await expect(tp.getForm()).toBeVisible();
});

test('can create a new transaction', async ({ page }) => {
	const tp = new TransactionsPage(page);
	await tp.goto();

	const initialCount = await tp.getRows().count();

	await tp.fillCreateForm({
		date: currentMonthDate(15),
		label: 'Test Transaction E2E',
		amount: '42.00',
		mode: 'debit',
	});
	await tp.submitCreate();

	// Wait for list to update
	await expect(tp.getRows()).toHaveCount(initialCount + 1);
	await expect(page.locator('text=Test Transaction E2E')).toBeVisible();
});

test('can edit a transaction', async ({ page }) => {
	const tp = new TransactionsPage(page);
	await tp.goto();

	// Wait for rows to be present
	await expect(tp.getRows().first()).toBeVisible();

	const firstRow = tp.getRows().first();
	await tp.clickEditOnRow(firstRow);

	// Edit form should appear
	const editRow = tp.getEditRows().first();
	await expect(editRow).toBeVisible();

	// Change the label
	await editRow.locator('input[name="label"]').fill('Updated Label E2E');
	await tp.saveEditRow(editRow);

	// Should go back to row view with updated label
	await expect(tp.getRows().first()).toBeVisible();
	await expect(page.locator('text=Updated Label E2E')).toBeVisible();
});

test('can cancel editing a transaction', async ({ page }) => {
	const tp = new TransactionsPage(page);
	await tp.goto();

	await expect(tp.getRows().first()).toBeVisible();

	const firstRow = tp.getRows().first();
	await tp.clickEditOnRow(firstRow);

	const editRow = tp.getEditRows().first();
	await expect(editRow).toBeVisible();

	await tp.cancelEditRow(editRow);

	// Should return to row view (no edit rows visible)
	await expect(tp.getEditRows()).toHaveCount(0);
});

test('can delete a transaction', async ({ page }) => {
	const tp = new TransactionsPage(page);
	await tp.goto();

	await expect(tp.getRows().first()).toBeVisible();
	const initialCount = await tp.getRows().count();

	const firstRow = tp.getRows().first();

	// Handle the confirm dialog
	page.once('dialog', (dialog) => dialog.accept());
	await tp.clickDeleteOnRow(firstRow);

	// Row count should decrease
	await expect(tp.getRows()).toHaveCount(initialCount - 1);
});

test('filter bar is visible', async ({ page }) => {
	const tp = new TransactionsPage(page);
	await tp.goto();
	await expect(tp.getFilterForm()).toBeVisible();
	await expect(tp.getLabelSearch()).toBeVisible();
});

test('label filter narrows results', async ({ page }) => {
	const tp = new TransactionsPage(page);
	await tp.goto();

	// First create a transaction with a unique label
	await tp.fillCreateForm({
		label: 'UniqueFilterLabel99',
		amount: '5.00',
		mode: 'debit',
	});
	await tp.submitCreate();

	// Now filter by the unique label
	await tp.getLabelSearch().fill('UniqueFilterLabel99');
	// Trigger filter (keyup)
	await tp.getLabelSearch().press('a');
	await tp.getLabelSearch().press('Backspace');

	// Wait for filtered results
	await page.waitForTimeout(500);
	await expect(page.locator('text=UniqueFilterLabel99')).toBeVisible();
	const rows = await tp.getRows().count();
	expect(rows).toBeGreaterThanOrEqual(1);
});

test('URL updates with filter params after preset change', async ({ page }) => {
	const tp = new TransactionsPage(page);
	await tp.goto();

	await tp.getPresetButton('last_month').click();
	await page.waitForTimeout(300);

	expect(page.url()).toContain('date_preset=last_month');
});

function parseCents(text: string): number {
	// Handles "$1.23" and "-$1.23"
	const m = text.replace(/\s/g, '').match(/^(-?)\\$([0-9]+)\\.([0-9]{2})$/);
	if (!m) return NaN;
	const sign = m[1] === '-' ? -1 : 1;
	return sign * (parseInt(m[2]) * 100 + parseInt(m[3]));
}

test('daily total updates after create and delete', async ({ page }) => {
	const tp = new TransactionsPage(page);
	// Use all_time preset so the target date is always visible
	await page.goto('/transactions?date_preset=all_time');

	// Pick a fixed date in the current month unlikely to have existing transactions
	const now = new Date();
	const year = now.getFullYear();
	const month = String(now.getMonth() + 1).padStart(2, '0');
	const isoDate = `${year}-${month}-03`;
	// The server formats dates as "Jan 02, 2006"
	const fmtDate = new Date(`${isoDate}T12:00:00`).toLocaleDateString('en-US', {
		month: 'short',
		day: '2-digit',
		year: 'numeric',
	});

	// Record the subtotal before (may not exist if no transactions on that day)
	const subtotalLocator = tp.getDailySubtotal(fmtDate);
	const subtotalTextBefore = (await subtotalLocator.isVisible())
		? (await subtotalLocator.textContent()) ?? ''
		: null;

	// Create a debit transaction of $10.00 on the target date
	await tp.fillCreateForm({ date: isoDate, label: 'DailyTotalTest', amount: '10.00', mode: 'debit' });
	await tp.submitCreate();

	// Wait for the new row to appear (confirms HTMX swap completed)
	const newRow = tp.getRows().filter({ hasText: 'DailyTotalTest' }).first();
	await expect(newRow).toBeVisible();

	// Daily subtotal should now differ from the pre-create value
	const subtotalTextAfterCreate = (await subtotalLocator.textContent()) ?? '';
	expect(subtotalTextAfterCreate).not.toBe(subtotalTextBefore ?? '');

	// Delete the transaction we just created
	page.once('dialog', (dialog) => dialog.accept());
	await tp.clickDeleteOnRow(newRow);
	await expect(newRow).not.toBeVisible();

	// Daily subtotal should return to what it was before (or the group should disappear)
	if (subtotalTextBefore === null) {
		// The day group should be gone entirely since we added the only transaction
		await expect(subtotalLocator).not.toBeVisible();
	} else {
		// Subtotal should revert to the pre-create value
		await expect(subtotalLocator).toHaveText(subtotalTextBefore);
	}
});

test('URL params restore filters on reload', async ({ page }) => {
	const tp = new TransactionsPage(page);
	// Navigate directly with filter params
	await page.goto('/transactions?date_preset=all_time&account_type=expenses');

	await expect(tp.getList()).toBeVisible();
	await expect(tp.getPresetButton('all_time')).toHaveClass(/bg-emerald-600/);

	// Reload and verify filter is preserved
	await page.reload();
	await expect(tp.getPresetButton('all_time')).toHaveClass(/bg-emerald-600/);
});

test('transaction create rejects blank labels', async ({ request }) => {
	const response = await request.post('/transactions', {
		form: {
			date: currentMonthDate(15),
			label: '   ',
			amount: '10.00',
			amount_mode: 'debit',
			account_id: '3',
			category_id: '0',
			account_type: 'expenses'
		}
	});

	expect(response.status()).toBe(400);
	await expect(response.text()).resolves.toContain('transaction label is required');
});

test('transaction create rejects zero amounts', async ({ request }) => {
	const response = await request.post('/transactions', {
		form: {
			date: currentMonthDate(15),
			label: 'Zero Amount',
			amount: '0.00',
			amount_mode: 'debit',
			account_id: '3',
			category_id: '0',
			account_type: 'expenses'
		}
	});

	expect(response.status()).toBe(400);
	await expect(response.text()).resolves.toContain('transaction amount must be non-zero');
});

test('transaction update rejects invalid dates', async ({ request }) => {
	const listResponse = await request.get('/transactions?date_preset=all_time');
	const html = await listResponse.text();
	const match = html.match(/id="transaction-(\d+)"/);
	expect(match).not.toBeNull();

	const response = await request.put(`/transactions/${match![1]}`, {
		form: {
			date: 'not-a-date',
			label: 'Still Valid',
			amount: '10.00',
			amount_mode: 'debit',
			account_id: '3',
			category_id: '0'
		}
	});

	expect(response.status()).toBe(400);
	await expect(response.text()).resolves.toContain('transaction date must be YYYY-MM-DD');
});
