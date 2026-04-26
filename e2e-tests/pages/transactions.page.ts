import type { Page, Locator } from '@playwright/test';

export class TransactionsPage {
	constructor(private page: Page) {}

	async goto() {
		await this.page.goto('/transactions');
	}

	getList(): Locator {
		return this.page.locator('[data-testid="transaction-list"]');
	}

	getRows(): Locator {
		return this.page.locator('[data-testid="transaction-row"]');
	}

	getEditRows(): Locator {
		return this.page.locator('[data-testid="transaction-row-edit"]');
	}

	getForm(): Locator {
		return this.page.locator('#transaction-form');
	}

	getCreateDateInput(): Locator {
		return this.getForm().locator('input[name="date"]');
	}

	getCreateLabelInput(): Locator {
		return this.getForm().locator('input[name="label"]');
	}

	getCreateAmountInput(): Locator {
		return this.getForm().locator('input[name="amount"]');
	}

	getCreateAmountModeSelect(): Locator {
		return this.getForm().locator('select[name="amount_mode"]');
	}

	getCreateAccountSelect(): Locator {
		return this.getForm().locator('select[name="account_id"]');
	}

	getCreateCategorySelect(): Locator {
		return this.getForm().locator('select[name="category_id"]');
	}

	getCreateStatus(): Locator {
		return this.page.locator('[data-testid="transaction-form-status"]');
	}

	getDateTodayButton(): Locator {
		return this.page.locator('[data-testid="transaction-date-today"]');
	}

	getDateNotice(): Locator {
		return this.page.locator('[data-testid="transaction-date-notice"]');
	}

	getDateNoticeUseToday(): Locator {
		return this.page.locator('[data-testid="transaction-date-use-today"]');
	}

	getDateNoticeKeepDate(): Locator {
		return this.page.locator('[data-testid="transaction-date-keep"]');
	}

	getRecommendationPanel(): Locator {
		return this.page.locator('[data-testid="transaction-category-recommendation"]');
	}

	getRecommendationApply(): Locator {
		return this.page.locator('[data-testid="transaction-category-apply"]');
	}

	getRecommendationLabel(): Locator {
		return this.page.locator('[data-testid="transaction-category-label"]');
	}

	async fillCreateForm(opts: {
		date?: string;
		label: string;
		amount: string;
		mode?: 'debit' | 'credit';
		categoryId?: string;
		accountId?: string;
	}) {
		const form = this.getForm();
		if (opts.date) {
			await form.locator('input[name="date"]').fill(opts.date);
		}
		await form.locator('input[name="label"]').fill(opts.label);
		await form.locator('input[name="amount"]').fill(opts.amount);
		if (opts.mode) {
			await form.locator('select[name="amount_mode"]').selectOption(opts.mode);
		}
		if (opts.categoryId) {
			await form.locator('select[name="category_id"]').selectOption(opts.categoryId);
		}
		if (opts.accountId) {
			await form.locator('select[name="account_id"]').selectOption(opts.accountId);
		}
	}

	async submitCreate() {
		await this.getForm().locator('button[type="submit"]').click();
	}

	async applyRecommendation() {
		await this.getRecommendationApply().click();
	}

	async clickEditOnRow(rowLocator: Locator) {
		await rowLocator.hover();
		await rowLocator.locator('button:has-text("Edit")').click();
	}

	async clickDeleteOnRow(rowLocator: Locator) {
		await rowLocator.hover();
		await rowLocator.locator('button:has-text("Delete")').click();
	}

	async saveEditRow(editRowLocator: Locator) {
		await editRowLocator.locator('button:has-text("Save")').click();
	}

	async cancelEditRow(editRowLocator: Locator) {
		await editRowLocator.locator('button:has-text("Cancel")').click();
	}

	getFilterForm(): Locator {
		return this.page.locator('#transaction-filters');
	}

	getLabelSearch(): Locator {
		return this.page.locator('#label-search');
	}

	getPresetButton(preset: string): Locator {
		return this.page.locator(`button[hx-vals*="${preset}"]`);
	}

	// Returns the subtotal element for a given date group (date formatted as "Jan 02, 2006")
	getDailySubtotal(formattedDate: string): Locator {
		return this.page.locator(
			`[data-testid="transaction-group"][data-date="${formattedDate}"] [data-testid="transaction-subtotal"]`
		);
	}

	getDateGroup(formattedDate: string): Locator {
		return this.page.locator(`[data-testid="transaction-group"][data-date="${formattedDate}"]`);
	}

	getRowInGroup(formattedDate: string, label: string): Locator {
		return this.getDateGroup(formattedDate)
			.locator('[data-testid="transaction-row"]')
			.filter({ hasText: label });
	}
}
