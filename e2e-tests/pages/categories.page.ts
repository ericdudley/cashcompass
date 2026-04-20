import type { Page, Locator } from '@playwright/test';

export class CategoriesPage {
	constructor(private page: Page) {}

	async goto() {
		await this.page.goto('/categories');
	}

	async createCategory(label: string) {
		await this.page.fill('#cat-label', label);
		await this.page.click('button[type="submit"]');
		await this.page.waitForSelector(`[data-label="${label}"]`);
	}

	async editLabel(currentLabel: string, newLabel: string) {
		await this.getCard(currentLabel).locator('button[title="Edit label"]').click();
		const input = this.page.locator(`[data-label="${currentLabel}"] input[name="label"]`);
		await input.waitFor({ state: 'visible' });
		await input.fill(newLabel);
		await this.getCard(currentLabel).locator('button:has-text("Save")').click();
		await this.page.waitForSelector(`[data-label="${newLabel}"]`);
	}

	async cancelEdit(label: string) {
		await this.getCard(label).locator('button[title="Edit label"]').click();
		const input = this.page.locator(`[data-label="${label}"] input[name="label"]`);
		await input.waitFor({ state: 'visible' });
		await this.getCard(label).locator('button:has-text("Cancel")').click();
		await input.waitFor({ state: 'detached' });
		await this.page.waitForSelector(`[data-label="${label}"]`);
	}

	async deleteCategory(label: string) {
		this.page.once('dialog', (dialog) => dialog.accept());
		await this.getCard(label).locator('button:has-text("Delete")').click();
		await this.page.locator(`[data-label="${label}"]`).waitFor({ state: 'detached' });
	}

	getCard(label: string): Locator {
		return this.page.locator(`[data-label="${label}"]`);
	}

	getList(): Locator {
		return this.page.locator('[data-testid="categories"]');
	}
}
