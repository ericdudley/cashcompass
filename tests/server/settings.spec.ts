import { test, expect } from './fixtures';
import { SettingsPage } from './pages/settings.page';

test('settings page loads', async ({ page }) => {
	const sp = new SettingsPage(page);
	await sp.goto();

	await expect(page.locator('h1')).toContainText('Settings');
	await expect(sp.getExpensesSection()).toBeVisible();
	await expect(sp.getAccountsSection()).toBeVisible();
	await expect(sp.getResetSection()).toBeVisible();
});

test('expenses export returns CSV', async ({ request }) => {
	const response = await request.get('/settings/export/expenses');

	expect(response.ok()).toBeTruthy();
	expect(response.headers()['content-type']).toContain('text/csv');
	await expect(response.text()).resolves.toContain('Amount,Category,Date,Description');
	await expect(response.text()).resolves.toContain('Weekly shop');
});

test('accounts export returns CSV', async ({ request }) => {
	const response = await request.get('/settings/export/accounts');

	expect(response.ok()).toBeTruthy();
	expect(response.headers()['content-type']).toContain('text/csv');
	await expect(response.text()).resolves.toBe('Account,Date,Balance\r\n');
});

test('expenses import success path works', async ({ request, page }) => {
	const csv = [
		'Amount,Category,Date,Description',
		'12.34,Coffee,2026-04-19T08:15:00-07:00,Morning coffee',
		'9.99,Snacks,2026-04-19,Snack run'
	].join('\n');

	const response = await request.post('/settings/import/expenses', {
		multipart: {
			timezone: 'America/Los_Angeles',
			file: {
				name: 'expenses.csv',
				mimeType: 'text/csv',
				buffer: Buffer.from(csv)
			}
		}
	});

	expect(response.ok()).toBeTruthy();
	await expect(response.text()).resolves.toContain('Imported 2 expense transaction(s) successfully.');

	const exportResponse = await request.get('/settings/export/expenses');
	const exportCsv = await exportResponse.text();
	expect(exportCsv).toContain('Morning coffee');
	expect(exportCsv).toContain('Snack run');

	const sp = new SettingsPage(page);
	await page.goto('/settings?imported=expenses&count=2');
	await expect(sp.getSuccessAlert()).toContainText('Imported 2 expense transaction(s) successfully.');
});

test('accounts import success path works', async ({ request, page }) => {
	const csv = [
		'Account,Date,Balance',
		'Brokerage,2026-03-15,1000.00',
		'Brokerage,2026-04-15T23:30:00-07:00,1250.50'
	].join('\n');

	const response = await request.post('/settings/import/accounts', {
		multipart: {
			timezone: 'America/Los_Angeles',
			file: {
				name: 'accounts.csv',
				mimeType: 'text/csv',
				buffer: Buffer.from(csv)
			}
		}
	});

	expect(response.ok()).toBeTruthy();
	await expect(response.text()).resolves.toContain('Imported 2 reconciliation transaction(s) successfully.');

	const exportResponse = await request.get('/settings/export/accounts');
	const exportCsv = await exportResponse.text();
	expect(exportCsv).toContain('Brokerage,2026-03-15,1000.00');
	expect(exportCsv).toContain('Brokerage,2026-04-15,1250.50');

	const sp = new SettingsPage(page);
	await page.goto('/settings?imported=accounts&count=2');
	await expect(sp.getSuccessAlert()).toContainText('Imported 2 reconciliation transaction(s) successfully.');
});

test('missing-column CSV shows an error', async ({ request, page }) => {
	const csv = [
		'Amount,Category,Date',
		'12.34,Coffee,2026-04-19'
	].join('\n');

	const response = await request.post('/settings/import/expenses', {
		multipart: {
			timezone: 'America/Los_Angeles',
			file: {
				name: 'bad-expenses.csv',
				mimeType: 'text/csv',
				buffer: Buffer.from(csv)
			}
		}
	});

	expect(response.ok()).toBeTruthy();
	await expect(response.text()).resolves.toContain('Error: missing column: Description');

	const sp = new SettingsPage(page);
	await page.goto('/settings?error=missing+column%3A+Description');
	await expect(sp.getErrorAlert()).toContainText('missing column: Description');
});

test('dev-only reset flow clears exported data', async ({ request, page }) => {
	const response = await request.post('/settings/reset-database');
	expect(response.ok()).toBeTruthy();

	const sp = new SettingsPage(page);
	await page.goto('/settings?reset=1');
	await expect(sp.getSuccessAlert()).toContainText('Database reset successfully.');

	const exportResponse = await request.get('/settings/export/expenses');
	await expect(exportResponse.text()).resolves.toBe('Amount,Category,Date,Description\r\n');
});
