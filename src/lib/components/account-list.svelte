<script lang="ts">
	import TrashIcon from 'virtual:icons/mdi/trash';
	import DisplayInput from './ui/display-input.svelte';
	import { liveQuery } from 'dexie';
	import { getDbContext } from '$lib/context';
	import AccountIcon from './ui/icons/account-icon.svelte';
	import type { Account } from '$lib/dexie/models/account';
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
</script>

<ul class="list-none flex flex-col gap-2">
	{#if $accounts}
		{#each $accounts as account}
			<li class="flex items-center justify-between">
				<span class="flex items-center text-sm font-medium me-3 gap-1">
					<AccountIcon />
					<DisplayInput
						value={account.label}
						onSave={(value) => onLabelChange(account.id, value)}
					/>
				</span>
				<div class="ml-auto">
					<div class="join">
						<button
							class="btn btn-xs join-item {account.accountType === 'expenses' && 'btn-active'}"
							onclick={() => onAccountTypeChange(account.id, 'expenses')}
						>
							Expenses
						</button>
						<button
							class="btn btn-xs join-item {account.accountType === 'net_worth' && 'btn-active'}"
							onclick={() => onAccountTypeChange(account.id, 'net_worth')}
						>
							Net Worth
						</button>
					</div>
					<button
						class="btn btn-square btn-sm btn-error btn-ghost"
						onclick={() => handleDelete(account.id)}
					>
						<TrashIcon />
					</button>
				</div>
			</li>
		{/each}
		{#if $accounts.length === 0}
			<li class="text-sm text-gray-500 mx-auto">No accounts found</li>
		{/if}
	{/if}
</ul>
