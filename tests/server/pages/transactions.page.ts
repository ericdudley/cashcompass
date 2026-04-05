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

	async fillCreateForm(opts: {
		date?: string;
		label: string;
		amount: string;
		mode?: 'debit' | 'credit';
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
	}

	async submitCreate() {
		await this.getForm().locator('button[type="submit"]').click();
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
}
