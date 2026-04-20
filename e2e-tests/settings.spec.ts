import { test, expect } from './fixtures';
import { SettingsPage } from './pages/settings.page';

function withoutExportedAt(payload: Record<string, unknown>) {
	const next = JSON.parse(JSON.stringify(payload));
	delete next.exported_at;
	return next;
}

test('settings page loads', async ({ page }) => {
	const sp = new SettingsPage(page);
	await sp.goto();

	await expect(page.locator('h1')).toContainText('Settings');
	await expect(sp.getThemeSection()).toBeVisible();
	await expect(sp.getBackupSection()).toBeVisible();
	await expect(sp.getTransactionsExportSection()).toBeVisible();
	await expect(sp.getResetSection()).toBeVisible();
});

test('theme selection from settings persists and syncs with nav', async ({ page }) => {
	const sp = new SettingsPage(page);
	await sp.goto();

	await sp.getThemePicker().selectOption('cupcake');
	await expect(sp.getThemePicker()).toHaveValue('cupcake');
	await expect(page.locator('html')).toHaveAttribute('data-theme', 'cupcake');
	await expect(page.locator('nav #theme-picker')).toHaveValue('cupcake');

	const storedTheme = await page.evaluate(() => window.localStorage.getItem('cashcompass-theme'));
	expect(storedTheme).toBe('cupcake');

	await page.reload();
	await expect(page.locator('html')).toHaveAttribute('data-theme', 'cupcake');
	await expect(sp.getThemePicker()).toHaveValue('cupcake');
	await expect(page.locator('nav #theme-picker')).toHaveValue('cupcake');
});

test('backup export returns canonical JSON', async ({ request }) => {
	const response = await request.get('/settings/export/backup');

	expect(response.ok()).toBeTruthy();
	expect(response.headers()['content-type']).toContain('application/json');

	const payload = await response.json();
	expect(payload.format).toBe('cashcompass.backup');
	expect(payload.version).toBe(1);
	expect(payload.app).toEqual({ name: 'CashCompass' });
	expect(payload.schema).toEqual({ entities: ['accounts', 'categories', 'transactions'] });
	expect(payload.accounts[0].id).toMatch(/^acct_/);
	expect(payload.categories[0].id).toMatch(/^cat_/);
	expect(payload.transactions[0].id).toMatch(/^txn_/);
});

test('transactions export returns interoperability CSV', async ({ request }) => {
	const response = await request.get('/settings/export/transactions.csv');

	expect(response.ok()).toBeTruthy();
	expect(response.headers()['content-type']).toContain('text/csv');

	const csv = await response.text();
	expect(csv).toContain('transaction_id,date,amount_cents,amount,label,account,account_type,category,archived_account');
	expect(csv).toContain('Weekly shop');
	expect(csv).toMatch(/txn_[a-f0-9]{32}/);
});

test('backup restore round-trip preserves archived and uncategorized data', async ({ request, page }) => {
	const initialResponse = await request.get('/settings/export/backup');
	const initialBackup = await initialResponse.json();

	const savings = initialBackup.accounts.find((acct: any) => acct.label === 'Savings');
	const dailyExpenses = initialBackup.accounts.find((acct: any) => acct.label === 'Daily Expenses');
	const checking = initialBackup.accounts.find((acct: any) => acct.label === 'Checking');

	expect(savings).toBeTruthy();
	expect(dailyExpenses).toBeTruthy();
	expect(checking).toBeTruthy();

	const archiveResponse = await request.put(`/accounts/${savings.legacy_numeric_id}/archive`);
	expect(archiveResponse.ok()).toBeTruthy();

	const uncategorizedResponse = await request.post('/transactions?account_type=expenses', {
		form: {
			date: '2026-04-19',
			label: 'No category expense',
			amount: '11.11',
			amount_mode: 'debit',
			account_id: String(dailyExpenses.legacy_numeric_id),
			category_id: '0'
		}
	});
	expect(uncategorizedResponse.ok()).toBeTruthy();

	const netWorthResponse = await request.post('/transactions?account_type=net_worth', {
		form: {
			date: '2026-04-19',
			label: 'Manual balance adjustment',
			amount: '1000.00',
			amount_mode: 'credit',
			account_id: String(checking.legacy_numeric_id),
			category_id: '0'
		}
	});
	expect(netWorthResponse.ok()).toBeTruthy();

	const backupResponse = await request.get('/settings/export/backup');
	const expectedBackup = await backupResponse.json();
	expect(expectedBackup.accounts.some((acct: any) => acct.is_archived)).toBe(true);
	expect(expectedBackup.transactions.some((txn: any) => txn.category_id === null)).toBe(true);
	expect(expectedBackup.transactions.some((txn: any) => txn.amount_cents === 100000)).toBe(true);
	expect(expectedBackup.accounts.some((acct: any) => acct.label.startsWith('Imported Expenses'))).toBe(false);

	const resetResponse = await request.post('/settings/reset-database');
	expect(resetResponse.ok()).toBeTruthy();

	const restoreResponse = await request.post('/settings/import/backup', {
		multipart: {
			file: {
				name: 'cashcompass-backup.json',
				mimeType: 'application/json',
				buffer: Buffer.from(JSON.stringify(expectedBackup))
			}
		}
	});
	expect(restoreResponse.ok()).toBeTruthy();
	await expect(restoreResponse.text()).resolves.toContain('Backup restored successfully.');

	const restoredResponse = await request.get('/settings/export/backup');
	const restoredBackup = await restoredResponse.json();

	expect(withoutExportedAt(restoredBackup)).toEqual(withoutExportedAt(expectedBackup));
	expect(restoredBackup.accounts.some((acct: any) => acct.label.startsWith('Imported Expenses'))).toBe(false);

	const sp = new SettingsPage(page);
	await page.goto('/settings?imported=backup');
	await expect(sp.getSuccessAlert()).toContainText('Backup restored successfully.');
});

test('backup import rejects unsupported version', async ({ request, page }) => {
	const response = await request.get('/settings/export/backup');
	const payload = await response.json();
	payload.version = 2;

	const importResponse = await request.post('/settings/import/backup', {
		multipart: {
			file: {
				name: 'bad-backup.json',
				mimeType: 'application/json',
				buffer: Buffer.from(JSON.stringify(payload))
			}
		}
	});

	expect(importResponse.ok()).toBeTruthy();
	await expect(importResponse.text()).resolves.toContain('Error: unsupported backup version');

	const sp = new SettingsPage(page);
	await page.goto('/settings?error=unsupported+backup+version');
	await expect(sp.getErrorAlert()).toContainText('unsupported backup version');
});

test('backup import rejects unresolved references', async ({ request, page }) => {
	const response = await request.get('/settings/export/backup');
	const payload = await response.json();
	payload.transactions[0].account_id = 'acct_missing';

	const importResponse = await request.post('/settings/import/backup', {
		multipart: {
			file: {
				name: 'bad-backup.json',
				mimeType: 'application/json',
				buffer: Buffer.from(JSON.stringify(payload))
			}
		}
	});

	expect(importResponse.ok()).toBeTruthy();
	await expect(importResponse.text()).resolves.toContain('Error: transaction account_id does not resolve');

	const sp = new SettingsPage(page);
	await page.goto('/settings?error=transaction+account_id+does+not+resolve%3A+acct_missing');
	await expect(sp.getErrorAlert()).toContainText('transaction account_id does not resolve');
});

test('legacy import and export endpoints are removed', async ({ request }) => {
	const endpoints = [
		['GET', '/settings/export/expenses'],
		['POST', '/settings/import/expenses'],
		['GET', '/settings/export/accounts'],
		['POST', '/settings/import/accounts']
	] as const;

	for (const [method, path] of endpoints) {
		const response = method === 'GET'
			? await request.get(path)
			: await request.post(path);
		expect(response.status(), `${method} ${path}`).toBe(404);
	}
});

test('dev-only reset flow clears backup data', async ({ request, page }) => {
	const response = await request.post('/settings/reset-database');
	expect(response.ok()).toBeTruthy();

	const sp = new SettingsPage(page);
	await page.goto('/settings?reset=1');
	await expect(sp.getSuccessAlert()).toContainText('Database reset successfully.');

	const exportResponse = await request.get('/settings/export/backup');
	const payload = await exportResponse.json();
	expect(payload.accounts).toEqual([]);
	expect(payload.categories).toEqual([]);
	expect(payload.transactions).toEqual([]);
});
