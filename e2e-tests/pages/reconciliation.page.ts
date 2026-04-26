import type { Locator, Page } from '@playwright/test';

export class ReconciliationPage {
	constructor(private page: Page) {}

	async goto() {
		await this.page.goto('/accounts/reconcile');
	}

	getForm(): Locator {
		return this.page.locator('[data-testid="reconcile-form"]');
	}

	getRows(): Locator {
		return this.page.locator('[data-testid="reconcile-row"]');
	}

	getRow(label: string): Locator {
		return this.page.locator(`[data-testid="reconcile-row"][data-label="${label}"]`);
	}

	getCurrentBalance(label: string): Locator {
		return this.getRow(label).locator('[data-testid="reconcile-current-balance"]');
	}

	getLatestBalanceInput(label: string): Locator {
		return this.getRow(label).locator('input[data-reconcile-input="true"]');
	}

	getDiff(label: string): Locator {
		return this.getRow(label).locator('[data-testid="reconcile-diff"]');
	}

	getTotalDiff(): Locator {
		return this.page.locator('[data-testid="reconcile-total-diff"]');
	}

	getSuccessAlert(): Locator {
		return this.page.locator('[data-testid="reconcile-alert-success"]');
	}

	getStatusAlert(): Locator {
		return this.page.locator('[data-testid="reconcile-alert-status"]');
	}

	getErrorAlert(): Locator {
		return this.page.locator('[data-testid="reconcile-alert-error"]');
	}

	async save() {
		await this.getForm().locator('button[type="submit"]').click();
	}
}
