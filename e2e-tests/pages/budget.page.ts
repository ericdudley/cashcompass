import type { Locator, Page } from '@playwright/test';

export class BudgetPage {
	constructor(private page: Page) {}

	async goto(month = '2024-02') {
		await this.page.goto(`/budget?month=${month}`);
	}

	getMonth(): Locator {
		return this.page.locator('#budget-month');
	}

	getRows(): Locator {
		return this.page.getByTestId('budget-category-row');
	}

	getCategory(id: string): Locator {
		return this.page.locator(`[data-testid="budget-category-row"][data-category-id="${id}"]`);
	}

	getLimitInput(id: string): Locator {
		return this.page.locator(`#budget-limit-${id}`);
	}

	getLimitCard(id: string): Locator {
		return this.page.locator(`[data-testid="budget-limit-card"][data-category-id="${id}"]`);
	}

	async saveLimits() {
		await this.page.getByRole('button', { name: 'Save limits', exact: true }).click();
		await this.page.getByTestId('budget-saved').waitFor();
	}

	getTotal(kind: 'spending' | 'credits' | 'net'): Locator {
		return this.page.getByTestId(`category-total-${kind}`);
	}

	async selectMonth(month: string) {
		await this.getMonth().fill(month);
		await this.page.getByRole('button', { name: 'Go', exact: true }).click();
	}
}
