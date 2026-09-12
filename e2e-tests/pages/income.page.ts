import type { Page, Locator } from '@playwright/test';

export class IncomePage {
	constructor(private page: Page) {}

	async goto() {
		await this.page.goto('/income');
	}

	getForm(): Locator {
		return this.page.locator('#annual-income-form');
	}

	getList(): Locator {
		return this.page.locator('#annual-income-list');
	}

	getCards(): Locator {
		return this.page.locator('[data-testid="annual-income-card"]');
	}

	getCard(year: number): Locator {
		return this.page.locator(`[data-testid="annual-income-card"][data-year="${year}"]`);
	}

	async create(opts: {
		year: number;
		gross: string;
		federalTax?: string;
		stateTax?: string;
		notes?: string;
	}) {
		await this.getForm().locator('[name="tax_year"]').fill(String(opts.year));
		await this.getForm().locator('[name="gross_income"]').fill(opts.gross);
		await this.getForm().locator('[name="federal_tax"]').fill(opts.federalTax ?? '0');
		await this.getForm().locator('[name="state_tax"]').fill(opts.stateTax ?? '0');
		if (opts.notes) await this.getForm().locator('[name="notes"]').fill(opts.notes);
		await this.getForm().locator('button[type="submit"]').click();
		await this.getCard(opts.year).waitFor({ state: 'visible' });
	}
}
