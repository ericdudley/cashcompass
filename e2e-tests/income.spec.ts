import { test, expect } from './fixtures';
import { IncomePage } from './pages/income.page';

test('annual income page creates, edits, links, and deletes a tax year', async ({ page }) => {
	const income = new IncomePage(page);
	await income.goto();

	await expect(page.locator('h1')).toContainText('Annual Income');
	await expect(page.locator('[data-testid="annual-income-empty"]')).toBeVisible();

	await income.create({
		year: 2024,
		gross: '125000.00',
		federalTax: '22000.00',
		stateTax: '7000.00',
		notes: 'Backfilled from 2024 returns',
	});

	const card = income.getCard(2024);
	await expect(card).toContainText('$125,000.00');
	await expect(card).toContainText('$96,000.00 after listed taxes');
	await expect(card).toContainText('Backfilled from 2024 returns');
	await expect(card.locator('a[href="/flow?year=2024"]')).toBeVisible();

	await card.locator('button:has-text("Edit")').click();
	const edit = page.locator('[data-testid="annual-income-edit-form"]');
	await edit.locator('[name="state_tax"]').fill('7500.00');
	await edit.locator('button[type="submit"]').click();
	await expect(income.getCard(2024)).toContainText('$95,500.00 after listed taxes');

	page.once('dialog', (dialog) => dialog.accept());
	await income.getCard(2024).locator('button:has-text("Delete")').click();
	await expect(page.locator('[data-testid="annual-income-empty"]')).toBeVisible();
});

test('annual income validates duplicates and tax totals', async ({ request }) => {
	const first = await request.post('/income', {
		form: {
			tax_year: '2023',
			gross_income: '100000.00',
			federal_tax: '15000.00',
			state_tax: '5000.00',
		},
	});
	expect(first.ok()).toBeTruthy();

	const duplicate = await request.post('/income', {
		form: {
			tax_year: '2023',
			gross_income: '110000.00',
			federal_tax: '16000.00',
			state_tax: '6000.00',
		},
	});
	expect(duplicate.status()).toBe(400);
	await expect(duplicate.text()).resolves.toContain('already exists');

	const invalid = await request.post('/income', {
		form: {
			tax_year: '2022',
			gross_income: '10000.00',
			federal_tax: '9000.00',
			state_tax: '2000.00',
		},
	});
	expect(invalid.status()).toBe(400);
	await expect(invalid.text()).resolves.toContain('cannot exceed gross income');
});
