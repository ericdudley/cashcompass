import { test, expect } from './fixtures';
import { AccountsPage } from './pages/accounts.page';

test('create account', async ({ page }) => {
	const ap = new AccountsPage(page);
	await ap.goto();

	await ap.createAccount('TestCreate', 'net_worth');

	await expect(ap.getCard('TestCreate')).toBeVisible();
	await expect(ap.getActiveSection()).toContainText('TestCreate');
});

test('create account with expenses type', async ({ page }) => {
	const ap = new AccountsPage(page);
	await ap.goto();

	await ap.createAccount('TestExpenses', 'expenses');

	const card = ap.getCard('TestExpenses');
	await expect(card).toBeVisible();
	await expect(card).toContainText('expenses');
});

test('edit label via overlay — save', async ({ page }) => {
	const ap = new AccountsPage(page);
	await ap.goto();

	await ap.createAccount('EditMe', 'net_worth');
	await ap.editLabel('EditMe', 'EditedLabel');

	await expect(ap.getCard('EditedLabel')).toBeVisible();
	await expect(page.locator('[data-label="EditMe"]')).not.toBeAttached();
});

test('edit label via overlay — cancel', async ({ page }) => {
	const ap = new AccountsPage(page);
	await ap.goto();

	await ap.createAccount('CancelEdit', 'net_worth');
	await ap.cancelEdit('CancelEdit');

	await expect(ap.getCard('CancelEdit')).toBeVisible();
});

test('toggle account type', async ({ page }) => {
	const ap = new AccountsPage(page);
	await ap.goto();

	await ap.createAccount('TypeToggle', 'net_worth');
	const card = ap.getCard('TypeToggle');
	await expect(card).toContainText('net_worth');

	await ap.toggleType('TypeToggle');
	await expect(card).toContainText('expenses');

	await ap.toggleType('TypeToggle');
	await expect(card).toContainText('net_worth');
});

test('archive and unarchive', async ({ page }) => {
	const ap = new AccountsPage(page);
	await ap.goto();

	await ap.createAccount('ArchiveMe', 'net_worth');

	// Archive
	await ap.archiveAccount('ArchiveMe');

	// Card should move to archived section
	await expect(ap.getArchivedSection()).toContainText('ArchiveMe');
	await expect(ap.getActiveSection()).not.toContainText('ArchiveMe');

	// Unarchive
	await ap.unarchiveAccount('ArchiveMe');

	await expect(ap.getActiveSection()).toContainText('ArchiveMe');
	// Archived section should either be gone or not contain 'ArchiveMe'
	await expect(ap.getArchivedSection()).not.toBeAttached();
});

test('delete account with confirm', async ({ page }) => {
	const ap = new AccountsPage(page);
	await ap.goto();

	await ap.createAccount('DeleteMe', 'expenses');
	await expect(ap.getCard('DeleteMe')).toBeVisible();

	await ap.deleteAccount('DeleteMe');

	await expect(page.locator('[data-label="DeleteMe"]')).not.toBeAttached();
});

test('archived accounts appear in separate section', async ({ page }) => {
	const ap = new AccountsPage(page);
	await ap.goto();

	await ap.createAccount('ActiveAccount', 'net_worth');
	await ap.createAccount('ArchivedAccount', 'net_worth');
	await ap.archiveAccount('ArchivedAccount');

	await expect(ap.getActiveSection()).toContainText('ActiveAccount');
	await expect(ap.getActiveSection()).not.toContainText('ArchivedAccount');
	await expect(ap.getArchivedSection()).toContainText('ArchivedAccount');
	await expect(ap.getArchivedSection()).not.toContainText('ActiveAccount');
});
