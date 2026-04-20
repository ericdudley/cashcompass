import type { Page, Locator } from '@playwright/test';

export class SettingsPage {
	constructor(private page: Page) {}

	async goto() {
		await this.page.goto('/settings');
	}

	getThemeSection(): Locator {
		return this.page.locator('[data-testid="settings-theme-section"]');
	}

	getBackupSection(): Locator {
		return this.page.locator('[data-testid="settings-backup-section"]');
	}

	getTransactionsExportSection(): Locator {
		return this.page.locator('[data-testid="settings-transactions-export-section"]');
	}

	getThemePicker(): Locator {
		return this.page.locator('#settings-theme-picker');
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
