import type { Locator, Page } from '@playwright/test';

export class BudgetPage {
	constructor(private page: Page) {}

	async goto(month = '2024-02') {
		await this.page.goto(`/budget?month=${month}`);
	}

	async gotoAnnual(year = '2024') {
		await this.page.goto(`/budget?view=annual&year=${year}`);
	}

	getMonth(): Locator { return this.page.locator('#budget-month'); }
	getRows(): Locator { return this.page.getByTestId('budget-category-row'); }
	getCategory(id: string): Locator {
		return this.page.locator(`[data-testid="budget-category-row"][data-category-id="${id}"]`);
	}
	getLimitCard(id: string): Locator {
		return this.page.locator(`[data-testid="budget-limit-card"][data-category-id="${id}"]`);
	}
	getStatus(id: string): Locator { return this.getLimitCard(id).getByTestId('budget-limit-status'); }
	getBar(id: string): Locator { return this.getLimitCard(id).getByTestId('budget-bar'); }
	getAmount(): Locator { return this.page.locator('#budget-amount'); }

	async openEdit(id: string) {
		await this.getLimitCard(id).getByRole('link', { name: /^Edit .* budget$/ }).click();
		await this.page.getByTestId('budget-edit-form').waitFor();
	}
	async saveBudget() {
		await this.page.getByRole('button', { name: 'Save budget', exact: true }).click();
		await this.page.getByTestId('budget-saved').waitFor();
	}
	async edit(id: string, amount: string, options: { period?: 'monthly' | 'annual'; rollover?: boolean; effectiveMonth?: string } = {}) {
		await this.openEdit(id);
		if (options.period) await this.page.getByLabel('Budget type', { exact: true }).selectOption(options.period);
		await this.getAmount().fill(amount);
		if (options.rollover !== undefined) await this.page.getByRole('checkbox').setChecked(options.rollover);
		if (options.effectiveMonth) await this.page.getByLabel('Effective month', { exact: true }).fill(options.effectiveMonth);
		await this.saveBudget();
	}
	async openDetails(id: string) {
		await this.getLimitCard(id).getByText('Budget details', { exact: true }).click();
	}
	getTotal(kind: 'spending' | 'credits' | 'net'): Locator { return this.page.getByTestId(`category-total-${kind}`); }
	async selectMonth(month: string) {
		await this.getMonth().fill(month);
		await this.page.getByRole('button', { name: 'Go', exact: true }).click();
	}
}
