<script lang="ts">
	import TrashIcon from 'virtual:icons/mdi/trash';
	import DisplayInput from './ui/display-input.svelte';
	import { liveQuery } from 'dexie';
	import { getDbContext } from '$lib/context';
	import AccountIcon from './ui/icons/account-icon.svelte';
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

	async function handleChange(id: string, label: string) {
		// Update all transactions that reference this account
		db.transaction('rw', db.account, db.tx, async () => {
			await db.account.update(id, { label });

			await db.tx.where('account.id').equals(id).modify({ account: { id, label } });
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
					<DisplayInput value={account.label} onSave={(value) => handleChange(account.id, value)} />
				</span>
				<button
					class="btn btn-square btn-sm btn-error btn-ghost"
					onclick={() => handleDelete(account.id)}
				>
					<TrashIcon />
				</button>
			</li>
		{/each}
		{#if $accounts.length === 0}
			<li class="text-sm text-gray-500 mx-auto">No accounts found</li>
		{/if}
	{/if}
</ul>
