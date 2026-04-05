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
