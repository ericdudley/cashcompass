import type { Page, Locator } from '@playwright/test';

export class DashboardPage {
	constructor(private page: Page) {}

	async goto() {
		await this.page.goto('/dashboard');
	}

	getSummaryStats(): Locator {
		return this.page.locator('[data-testid="summary-stats"]');
	}

	getStatThisMonth(): Locator {
		return this.page.locator('[data-testid="stat-this-month"]');
	}

	getExpensesSection(): Locator {
		return this.page.locator('[data-testid="expenses-section"]');
	}

	getNetWorthSection(): Locator {
		return this.page.locator('[data-testid="net-worth-section"]');
	}

	getNetWorthChart(): Locator {
		return this.page.locator('[data-testid="net-worth-chart"]');
	}

	getNetWorthTable(): Locator {
		return this.page.locator('[data-testid="net-worth-table"]');
	}

	getCategoryTable(): Locator {
		return this.getExpensesSection().locator('table');
	}

	getCategoryRows(): Locator {
		return this.getCategoryTable().locator('tbody tr');
	}
}
