<script lang="ts">
	import { getDbContext } from '$lib/context';
	import type { Account } from '$lib/dexie/models/account';
	import { liveQuery } from 'dexie';
	import TrashIcon from 'virtual:icons/mdi/trash';
	import ArchiveIcon from 'virtual:icons/mdi/archive';
	import UnarchiveIcon from 'virtual:icons/mdi/unarchive';
	import EditableField from './ui/editable-field.svelte';
	import AccountIcon from './ui/icons/account-icon.svelte';
	import AccountListItem from './account-list-item.svelte';
	let { prefix }: { prefix: string } = $props();
	const db = getDbContext();

	let accounts = $derived.by(() => {
		// noop just to make it reactive
		prefix;

		return liveQuery(() =>
			db.account
				.where('label')
				.startsWithIgnoreCase(prefix ?? '')
				.toArray()
		);
	});

	let activeAccounts = $derived($accounts?.filter(account => account.isArchived === 0) ?? []);
	let archivedAccounts = $derived($accounts?.filter(account => account.isArchived === 1) ?? []);

	async function onLabelChange(id: string, label: string) {
		// Update all transactions that reference this account
		db.transaction('rw', db.account, db.tx, async () => {
			await db.account.update(id, { label });

			const newAccount = await db.account.get(id);

			await db.tx.where('account.id').equals(id).modify({ account: newAccount });
		});
	}

	async function onAccountTypeChange(id: string, accountType: Account['accountType']) {
		// Update all transactions that reference this account
		db.transaction('rw', db.account, db.tx, async () => {
			await db.account.update(id, { accountType });

			const newAccount = await db.account.get(id);

			await db.tx.where('account.id').equals(id).modify({ account: newAccount });
		});
	}

	async function handleDelete(id: string) {
		if (!confirm('Are you sure you want to delete this account?')) return;

		// Update all transactions that reference this account
		db.transaction('rw', db.account, db.tx, async () => {
			await db.account.delete(id);

			await db.tx.where('account.id').equals(id).modify({ account: undefined });
		});
	}

	async function toggleArchive(id: string, isArchived: 0 | 1) {
		await db.account.update(id, { isArchived });
	}
</script>

<div class="flex flex-col gap-4">
	<div>
		<h3 class="text-sm font-semibold mb-2">Active Accounts</h3>
		<ul class="list-none flex flex-col gap-2">
			{#if activeAccounts}
				{#each activeAccounts as account}
					<AccountListItem {account} />
				{/each}
				{#if activeAccounts.length === 0}
					<li class="text-sm text-gray-500 mx-auto">No active accounts found</li>
				{/if}
			{/if}
		</ul>
	</div>

	{#if archivedAccounts.length > 0}
		<div>
			<h3 class="text-sm font-semibold mb-2">Archived Accounts</h3>
			<ul class="list-none flex flex-col gap-2">
				{#each archivedAccounts as account}
					<AccountListItem {account} />
				{/each}
			</ul>
		</div>
	{/if}
</div>
