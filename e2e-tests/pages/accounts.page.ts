import type { Page, Locator } from '@playwright/test';

export class AccountsPage {
	constructor(private page: Page) {}

	async goto() {
		await this.page.goto('/accounts');
	}

	async createAccount(label: string, type: 'net_worth' | 'expenses') {
		await this.page.fill('#account-label', label);
		await this.page.selectOption('#account-type', type);
		await this.page.click('button[type="submit"]');
		await this.page.waitForSelector(`[data-label="${label}"]`);
	}

	async editLabel(currentLabel: string, newLabel: string) {
		await this.getCard(currentLabel).locator('button[title="Edit label"]').click();
		// Wait for the edit overlay to appear (it has an input)
		const input = this.page.locator(`[data-label="${currentLabel}"] input[name="label"]`);
		await input.waitFor({ state: 'visible' });
		await input.fill(newLabel);
		// Click Save button (has hx-put directly on it)
		await this.getCard(currentLabel).locator('button:has-text("Save")').click();
		await this.page.waitForSelector(`[data-label="${newLabel}"]`);
	}

	async cancelEdit(label: string) {
		await this.getCard(label).locator('button[title="Edit label"]').click();
		const input = this.page.locator(`[data-label="${label}"] input[name="label"]`);
		await input.waitFor({ state: 'visible' });
		await this.getCard(label).locator('button:has-text("Cancel")').click();
		// Card reverts to read view — input should be gone
		await input.waitFor({ state: 'detached' });
		await this.page.waitForSelector(`[data-label="${label}"]`);
	}

	async toggleType(label: string) {
		await this.getCard(label).locator('button:has-text("→")').click();
		await this.page.waitForSelector(`[data-label="${label}"]`);
	}

	async archiveAccount(label: string) {
		await this.getCard(label).locator('button:has-text("Archive")').click();
		// Archive re-renders the whole list; wait for the card to appear in archived section
		await this.page.locator(`[data-testid="archived-accounts"] [data-label="${label}"]`).waitFor({
			state: 'visible'
		});
	}

	async unarchiveAccount(label: string) {
		await this.getCard(label).locator('button:has-text("Unarchive")').click();
		// Unarchive re-renders the whole list; wait for the card to appear in active section
		await this.page.locator(`[data-testid="active-accounts"] [data-label="${label}"]`).waitFor({
			state: 'visible'
		});
	}

	async deleteAccount(label: string) {
		this.page.once('dialog', (dialog) => dialog.accept());
		await this.getCard(label).locator('button:has-text("Delete")').click();
		await this.page.locator(`[data-label="${label}"]`).waitFor({ state: 'detached' });
	}

	getCard(label: string): Locator {
		return this.page.locator(`[data-label="${label}"]`);
	}

	getActiveSection(): Locator {
		return this.page.locator('[data-testid="active-accounts"]');
	}

	getArchivedSection(): Locator {
		return this.page.locator('[data-testid="archived-accounts"]');
	}

	getReconcileLink(): Locator {
		return this.page.locator('[data-testid="accounts-reconcile-link"]');
	}
}
