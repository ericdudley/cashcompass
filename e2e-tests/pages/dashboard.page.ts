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

	getStatSelectedExpenses(): Locator {
		return this.page.locator('[data-testid="stat-selected-expenses"]');
	}

	getFilterTrigger(): Locator {
		return this.page.locator('[data-testid="dashboard-filter-trigger"]');
	}

	getFilters(): Locator {
		return this.page.locator('[data-testid="dashboard-filters"]');
	}

	getExpenseAccountFilter(): Locator {
		return this.page.locator('[data-testid="dashboard-expense-account-select"]');
	}

	getCategoryFilter(): Locator {
		return this.page.locator('[data-testid="dashboard-category-select"]');
	}

	getNetWorthAccountFilter(): Locator {
		return this.page.locator('[data-testid="dashboard-net-worth-account-select"]');
	}

	async openChecklist(filter: Locator) {
		await filter.locator('[data-cc-checklist-button]').click();
	}

	async clearChecklist(filter: Locator) {
		await this.openChecklist(filter);
		await filter.locator('[data-cc-checklist-clear]').click();
	}

	async checkChecklistOption(filter: Locator, label: string) {
		await this.openChecklist(filter);
		const row = filter.locator('[data-cc-checklist-row]').filter({ hasText: label }).first();
		const checkbox = row.locator('input[type="checkbox"]');
		if (!(await checkbox.isChecked())) {
			await row.click();
		}
	}

	getExpensesSection(): Locator {
		return this.page.locator('[data-testid="expenses-section"]');
	}

	getExpenseTrailingAverageLine(): Locator {
		return this.page.locator('[data-testid="expense-trailing-average-line"]');
	}

	getExpenseTrailingAveragePoints(): Locator {
		return this.page.locator('[data-testid="expense-trailing-average-points"]');
	}

	getExpenseYearMarkers(): Locator {
		return this.page.locator('[data-testid="expense-year-markers"]');
	}

	getExpenseBars(): Locator {
		return this.getExpensesSection().locator('.group.flex-1.flex.flex-col.items-end.justify-end.relative.h-full');
	}

	getExpenseMonthTooltips(): Locator {
		return this.page.locator('[data-testid="expense-month-tooltip"]');
	}

	getNetWorthSection(): Locator {
		return this.page.locator('[data-testid="net-worth-section"]');
	}

	getNetWorthChart(): Locator {
		return this.page.locator('[data-testid="net-worth-chart"]');
	}

	getNetWorthSegments(): Locator {
		return this.getNetWorthChart().locator('[data-nw-segment-label]');
	}

	getNetWorthBars(): Locator {
		return this.getNetWorthChart().locator('[data-nw-total]');
	}

	getNetWorthMonthTooltips(): Locator {
		return this.page.locator('[data-testid="net-worth-month-tooltip"]');
	}

	getNetWorthTrailingAverageLine(): Locator {
		return this.page.locator('[data-testid="net-worth-trailing-average-line"]');
	}

	getNetWorthTrailingAveragePoints(): Locator {
		return this.page.locator('[data-testid="net-worth-trailing-average-points"]');
	}

	getNetWorthYearMarkers(): Locator {
		return this.page.locator('[data-testid="net-worth-year-markers"]');
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
