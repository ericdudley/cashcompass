import { test, expect } from './fixtures';
import { TransactionsPage } from './pages/transactions.page';

// Current month date for creating transactions that appear in the default "this_month" filter.
function currentMonthDate(day = 15): string {
	const now = new Date();
	const year = now.getFullYear();
	const month = String(now.getMonth() + 1).padStart(2, '0');
	return `${year}-${month}-${String(day).padStart(2, '0')}`;
}

function formatDisplayDate(isoDate: string): string {
	return new Date(`${isoDate}T12:00:00`).toLocaleDateString('en-US', {
		month: 'short',
		day: '2-digit',
		year: 'numeric',
	});
}

function mockBrowserTodayScript(isoDate: string): string {
	return `
		(() => {
			const RealDate = Date;
			const fixedTime = new RealDate('${isoDate}T09:00:00').getTime();
			class MockDate extends RealDate {
				constructor(...args) {
					if (args.length === 0) {
						super(fixedTime);
					} else {
						super(...args);
					}
				}
				static now() {
					return fixedTime;
				}
			}
			window.Date = MockDate;
		})();
	`;
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
	await expect(tp.getPresetButton('this_month')).toHaveClass(/btn-primary/);
});

test('create form is visible', async ({ page }) => {
	const tp = new TransactionsPage(page);
	await tp.goto();
	await expect(tp.getForm()).toBeVisible();
});

test('category recommendation does not appear for incomplete form input', async ({ page }) => {
	const tp = new TransactionsPage(page);
	await tp.goto();

	await tp.getForm().locator('input[name="label"]').fill('Neighborhood market');
	await page.waitForTimeout(700);

	await expect(tp.getRecommendationPanel()).toHaveCount(1);
	await expect(tp.getRecommendationApply()).toHaveCount(0);
});

test('category recommendation appears and can be applied', async ({ page }) => {
	const tp = new TransactionsPage(page);
	await tp.goto();

	await tp.fillCreateForm({
		date: currentMonthDate(15),
		label: 'Neighborhood market',
		amount: '42.00',
		mode: 'debit',
	});

	await expect(tp.getRecommendationApply()).toBeVisible();
	await expect(tp.getRecommendationLabel()).toHaveText('Groceries');

	await tp.applyRecommendation();
	await expect(tp.getCreateCategorySelect()).toHaveValue('1');
});

test('user can override recommended category before submitting', async ({ page }) => {
	const tp = new TransactionsPage(page);
	await tp.goto();

	const initialCount = await tp.getRows().count();

	await tp.fillCreateForm({
		date: currentMonthDate(16),
		label: 'Neighborhood market',
		amount: '18.00',
		mode: 'debit',
	});

	await expect(tp.getRecommendationApply()).toBeVisible();
	await tp.applyRecommendation();
	await expect(tp.getCreateCategorySelect()).toHaveValue('1');

	await tp.getCreateCategorySelect().selectOption('2');
	await expect(tp.getCreateCategorySelect()).toHaveValue('2');

	await tp.submitCreate();

	await expect(tp.getRows()).toHaveCount(initialCount + 1);
	await expect(page.locator('text=Neighborhood market')).toBeVisible();
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

test('create form resets for repeated entry after adding a transaction', async ({ page }) => {
	const tp = new TransactionsPage(page);
	await tp.goto();

	const initialCount = await tp.getRows().count();
	const entryDate = currentMonthDate(17);

	await tp.fillCreateForm({
		date: entryDate,
		label: 'Repeated Entry E2E',
		amount: '19.50',
		mode: 'credit',
		categoryId: '2',
	});
	await tp.submitCreate();

	await expect(tp.getRows()).toHaveCount(initialCount + 1);
	await expect(tp.getCreateDateInput()).toHaveValue(entryDate);
	await expect(tp.getCreateAmountModeSelect()).toHaveValue('credit');
	await expect(tp.getCreateAccountSelect()).toHaveValue(/\d+/);
	await expect(tp.getCreateLabelInput()).toHaveValue('');
	await expect(tp.getCreateAmountInput()).toHaveValue('');
	await expect(tp.getCreateCategorySelect()).toHaveValue('0');
	await expect(tp.getRecommendationApply()).toHaveCount(0);
	await page.waitForTimeout(700);
	await expect(tp.getRecommendationApply()).toHaveCount(0);
	await expect(tp.getCreateStatus()).toContainText('Added. Ready for another transaction');
	await expect(tp.getCreateLabelInput()).toBeFocused();
});

test('stale empty create form advances to browser-local today', async ({ page }) => {
	await page.addInitScript(mockBrowserTodayScript('2099-01-02'));
	const tp = new TransactionsPage(page);
	await tp.goto();

	await expect(tp.getCreateDateInput()).toHaveValue('2099-01-02');
	await expect(tp.getDateNotice()).toBeHidden();
});

test('stale create form with a draft asks before changing the date', async ({ page }) => {
	const tp = new TransactionsPage(page);
	await tp.goto();

	await tp.getCreateDateInput().fill('2099-01-01');
	await tp.getCreateLabelInput().fill('Draft transaction');
	await page.evaluate(mockBrowserTodayScript('2099-01-02'));
	await page.evaluate(() => window.dispatchEvent(new Event('focus')));

	await expect(tp.getCreateDateInput()).toHaveValue('2099-01-01');
	await expect(tp.getDateNotice()).toBeVisible();
	await expect(tp.getDateNotice()).toContainText('This form is dated Jan 1. Today is Jan 2.');

	await tp.getDateNoticeKeepDate().click();
	await expect(tp.getCreateDateInput()).toHaveValue('2099-01-01');
	await expect(tp.getDateNotice()).toBeHidden();
});

test('stale create form notice can switch the draft to today', async ({ page }) => {
	const tp = new TransactionsPage(page);
	await tp.goto();

	await tp.getCreateDateInput().fill('2099-01-01');
	await tp.getCreateAmountInput().fill('10.00');
	await page.evaluate(mockBrowserTodayScript('2099-01-02'));
	await page.evaluate(() => window.dispatchEvent(new Event('focus')));

	await expect(tp.getDateNotice()).toBeVisible();
	await tp.getDateNoticeUseToday().click();

	await expect(tp.getCreateDateInput()).toHaveValue('2099-01-02');
	await expect(tp.getDateNotice()).toBeHidden();
});

test('today button updates the create form date', async ({ page }) => {
	await page.addInitScript(mockBrowserTodayScript('2099-01-02'));
	const tp = new TransactionsPage(page);
	await tp.goto();

	await tp.getCreateDateInput().fill('2099-01-01');
	await tp.getDateTodayButton().click();

	await expect(tp.getCreateDateInput()).toHaveValue('2099-01-02');
	await expect(tp.getDateNotice()).toBeHidden();
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

test('editing a transaction date moves it to the correct date group', async ({ page }) => {
	const tp = new TransactionsPage(page);
	await page.goto('/transactions?date_preset=all_time');

	const label = 'Weekly shop';
	const originalDate = currentMonthDate(1);
	const targetDate = currentMonthDate(15);
	const originalDisplayDate = formatDisplayDate(originalDate);
	const targetDisplayDate = formatDisplayDate(targetDate);

	const originalRow = tp.getRowInGroup(originalDisplayDate, label);
	await expect(originalRow).toBeVisible();

	await tp.clickEditOnRow(originalRow);

	const editRow = tp.getEditRows().first();
	await expect(editRow).toBeVisible();
	await editRow.locator('input[name="date"]').fill(targetDate);
	await tp.saveEditRow(editRow);

	await expect(tp.getRowInGroup(targetDisplayDate, label)).toBeVisible();
	await expect(tp.getRowInGroup(originalDisplayDate, label)).toHaveCount(0);
	await expect(tp.getDateGroup(originalDisplayDate)).toHaveCount(0);
	await expect(tp.getDailySubtotal(targetDisplayDate)).toHaveText('-$54.32');
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
	const fmtDate = formatDisplayDate(isoDate);

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
	await expect(tp.getPresetButton('all_time')).toHaveClass(/btn-primary/);

	// Reload and verify filter is preserved
	await page.reload();
	await expect(tp.getPresetButton('all_time')).toHaveClass(/btn-primary/);
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
