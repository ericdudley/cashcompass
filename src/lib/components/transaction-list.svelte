<script lang="ts">
	import TrashIcon from 'virtual:icons/mdi/trash';
	import DisplayInput from './ui/display-input.svelte';
	import { liveQuery } from 'dexie';
	import { getDbContext } from '$lib/context';
	import TransactionIcon from './ui/icons/transaction-icon.svelte';
	import { formatAmount } from '$lib/format';
	import CategoryPill from './category-pill.svelte';
	let { prefix }: { prefix: string } = $props();
	const db = getDbContext();

	let transactions = $derived.by(() => {
		// noop just to make it reactive
		prefix;

		return liveQuery(() =>
			db.tx
				.where('label')
				.startsWithIgnoreCase(prefix ?? '')
				.toArray()
		);
	});

	async function handleChange(id: string, label: string) {
		await db.tx.update(id, { label });
	}

	async function handleDelete(id: string) {
		if (!confirm('Are you sure you want to delete this transaction?')) return;

		await db.tx.delete(id);
	}
</script>

<ul class="list-none flex flex-col gap-2">
	{#if $transactions}
		{#each $transactions as transaction}
			<li class="flex items-center justify-between">
				<span class="flex items-center text-sm font-medium me-3 gap-1">
					<TransactionIcon />
					<span>
						{formatAmount(transaction.amount)}
					</span>

					<DisplayInput
						value={transaction.label ?? ''}
						onSave={(value) => handleChange(transaction.id, value)}
					/>
				</span>
				<div class="flex gap-1 items-center">
					{#if transaction.category}
						<CategoryPill label={transaction.category.label} />
					{/if}
					<button
						class="btn btn-square btn-sm btn-error btn-ghost"
						onclick={() => handleDelete(transaction.id)}
					>
						<TrashIcon />
					</button>
				</div>
			</li>
		{/each}
	{/if}
</ul>
