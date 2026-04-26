import { test, expect } from './fixtures';
import { AccountsPage } from './pages/accounts.page';
import { ReconciliationPage } from './pages/reconciliation.page';

function todayIsoDate(): string {
	return new Date().toISOString().slice(0, 10);
}

async function exportBackup(request: any) {
	const response = await request.get('/settings/export/backup');
	expect(response.ok()).toBeTruthy();
	return response.json();
}

async function getAccount(request: any, label: string) {
	const backup = await exportBackup(request);
	const account = backup.accounts.find((acct: any) => acct.label === label);
	expect(account).toBeTruthy();
	return account;
}

async function createNetWorthTransaction(request: any, accountLegacyId: number, label: string, amount: string) {
	const response = await request.post('/transactions?account_type=net_worth', {
		form: {
			date: todayIsoDate(),
			label,
			amount,
			amount_mode: 'credit',
			account_id: String(accountLegacyId),
			category_id: '0'
		}
	});
	expect(response.ok()).toBeTruthy();
}

test('accounts page links to reconciliation page', async ({ page }) => {
	const ap = new AccountsPage(page);
	await ap.goto();

	await ap.getReconcileLink().click();
	await expect(page).toHaveURL('/accounts/reconcile');
	await expect(page.locator('h1')).toContainText('Reconcile Net Worth');
});

test('reconciliation page shows active net worth accounts with current balances', async ({ page, request }) => {
	const checking = await getAccount(request, 'Checking');
	const savings = await getAccount(request, 'Savings');

	await createNetWorthTransaction(request, checking.legacy_numeric_id, 'Opening balance', '1000.00');
	await createNetWorthTransaction(request, savings.legacy_numeric_id, 'Opening balance', '250.50');

	const rp = new ReconciliationPage(page);
	await rp.goto();

	await expect(rp.getRow('Checking')).toBeVisible();
	await expect(rp.getCurrentBalance('Checking')).toHaveText('$1,000.00');
	await expect(rp.getRow('Savings')).toBeVisible();
	await expect(rp.getCurrentBalance('Savings')).toHaveText('$250.50');
	await expect(rp.getRows()).toHaveCount(2);
});

test('reconciliation page excludes archived net worth accounts', async ({ page, request }) => {
	const createResponse = await request.post('/accounts', {
		form: {
			label: 'Archived Brokerage',
			account_type: 'net_worth'
		}
	});
	expect(createResponse.ok()).toBeTruthy();

	const archived = await getAccount(request, 'Archived Brokerage');
	const archiveResponse = await request.put(`/accounts/${archived.legacy_numeric_id}/archive`);
	expect(archiveResponse.ok()).toBeTruthy();

	const rp = new ReconciliationPage(page);
	await rp.goto();

	await expect(rp.getRow('Archived Brokerage')).toHaveCount(0);
});

test('latest balances update diffs and total on the client', async ({ page, request }) => {
	const checking = await getAccount(request, 'Checking');
	const savings = await getAccount(request, 'Savings');

	await createNetWorthTransaction(request, checking.legacy_numeric_id, 'Opening balance', '1000.00');
	await createNetWorthTransaction(request, savings.legacy_numeric_id, 'Opening balance', '250.50');

	const rp = new ReconciliationPage(page);
	await rp.goto();

	await rp.getLatestBalanceInput('Checking').fill('1125.25');
	await rp.getLatestBalanceInput('Savings').fill('200.00');

	await expect(rp.getDiff('Checking')).toHaveText('+$125.25');
	await expect(rp.getDiff('Savings')).toHaveText('-$50.50');
	await expect(rp.getTotalDiff()).toHaveText('+$74.75');
});

test('saving adjustments creates non-zero diff transactions and refreshes balances', async ({ page, request }) => {
	const checking = await getAccount(request, 'Checking');
	const savings = await getAccount(request, 'Savings');

	await createNetWorthTransaction(request, checking.legacy_numeric_id, 'Opening balance', '1000.00');
	await createNetWorthTransaction(request, savings.legacy_numeric_id, 'Opening balance', '250.50');

	const rp = new ReconciliationPage(page);
	await rp.goto();

	await rp.getLatestBalanceInput('Checking').fill('1250.00');
	await rp.getLatestBalanceInput('Savings').fill('400.75');
	await rp.save();

	await expect(rp.getSuccessAlert()).toContainText('Created 2 adjustments.');
	await expect(rp.getCurrentBalance('Checking')).toHaveText('$1,250.00');
	await expect(rp.getCurrentBalance('Savings')).toHaveText('$400.75');

	const backup = await exportBackup(request);
	const adjustments = backup.transactions.filter((txn: any) => txn.label === 'Balance adjustment');
	expect(adjustments).toHaveLength(2);
	expect(adjustments.map((txn: any) => txn.amount_cents).sort((a: number, b: number) => a - b)).toEqual([15025, 25000]);
	expect(adjustments.every((txn: any) => txn.occurred_at === todayIsoDate())).toBe(true);
	expect(adjustments.every((txn: any) => txn.category_id === null)).toBe(true);
	expect(adjustments.map((txn: any) => txn.account_id).sort()).toEqual([checking.id, savings.id].sort());
});

test('zero diff saves no transactions and shows status message', async ({ page, request }) => {
	const rp = new ReconciliationPage(page);
	await rp.goto();

	await rp.getLatestBalanceInput('Checking').fill('0.00');
	await rp.save();

	await expect(rp.getStatusAlert()).toContainText('No balance adjustments were needed.');
	const backup = await exportBackup(request);
	expect(backup.transactions.filter((txn: any) => txn.label === 'Balance adjustment')).toHaveLength(0);
});

test('blank rows are ignored during save', async ({ page, request }) => {
	const checking = await getAccount(request, 'Checking');
	await createNetWorthTransaction(request, checking.legacy_numeric_id, 'Opening balance', '100.00');

	const rp = new ReconciliationPage(page);
	await rp.goto();

	await rp.getLatestBalanceInput('Checking').fill('125.00');
	await rp.save();

	await expect(rp.getSuccessAlert()).toContainText('Created 1 adjustment.');
	const backup = await exportBackup(request);
	const adjustments = backup.transactions.filter((txn: any) => txn.label === 'Balance adjustment');
	expect(adjustments).toHaveLength(1);
	expect(adjustments[0].amount_cents).toBe(2500);
});

test('invalid non-blank balances block the whole batch', async ({ page, request }) => {
	const savings = await getAccount(request, 'Savings');
	await createNetWorthTransaction(request, savings.legacy_numeric_id, 'Opening balance', '100.00');

	const rp = new ReconciliationPage(page);
	await rp.goto();

	await rp.getLatestBalanceInput('Checking').fill('oops');
	await rp.getLatestBalanceInput('Savings').fill('150.00');
	await rp.save();

	await expect(rp.getErrorAlert()).toContainText('Enter valid balances for every non-blank row.');
	const backup = await exportBackup(request);
	expect(backup.transactions.filter((txn: any) => txn.label === 'Balance adjustment')).toHaveLength(0);
	await expect(rp.getCurrentBalance('Savings')).toHaveText('$100.00');
});
