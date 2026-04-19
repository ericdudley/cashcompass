import type { Page, Locator } from '@playwright/test';

export class SettingsPage {
	constructor(private page: Page) {}

	async goto() {
		await this.page.goto('/settings');
	}

	getExpensesSection(): Locator {
		return this.page.locator('[data-testid="settings-expenses-section"]');
	}

	getAccountsSection(): Locator {
		return this.page.locator('[data-testid="settings-accounts-section"]');
	}

	getSuccessAlert(): Locator {
		return this.page.locator('[data-testid="settings-alert-success"]');
	}

	getErrorAlert(): Locator {
		return this.page.locator('[data-testid="settings-alert-error"]');
	}

	getResetSection(): Locator {
		return this.page.locator('[data-testid="settings-reset-section"]');
	}
}
