<script lang="ts">
	import { getDbContext } from '$lib/context';
	import { format, subDays } from 'date-fns';
	import { liveQuery } from 'dexie';
	import GroupedTransactionList from './grouped-transaction-list.svelte';
	import DateRangeInput from './ui/date-range-input.svelte';
	import LoadingStatus from './ui/loading-status.svelte';

	const db = getDbContext();

	let startDate = $state(subDays(new Date(), 30));
	let endDate = $state(new Date());
	let prefix = $state('');

	let txs = $derived.by(() => {
		// noop just to make it reactive
		prefix;
		startDate;
		endDate;

		return liveQuery(() =>
			db.tx
				.where('yyyyMMDd')
				.between(format(startDate, 'yyyy-MM-dd'), format(endDate, 'yyyy-MM-dd'), true, true)
				.and((tx) => (!!tx?.label?.startsWith ? tx.label.startsWith(prefix) : true))
				.sortBy('yyyyMMDd')
		);
	});

	async function handleChange(
		id: string,
		{
			label,
			amount,
			categoryId,
			unixMs
		}: { label: string; amount: number; categoryId?: string; unixMs?: number }
	) {
		if (categoryId) {
			const category = await db.category.get(categoryId);
			if (!category) {
				alert('Category not found');
				return;
			}
			await db.tx.update(id, { label, amount, category });
		} else {
			await db.tx.update(id, { label, amount });
		}

		if (unixMs) {
			await db.tx.update(id, { unixMs, yyyyMMDd: format(unixMs, 'yyyy-MM-dd') });
		}
	}

	async function handleDelete(id: string) {
		if (!confirm('Are you sure you want to delete this transaction?')) return;

		await db.tx.delete(id);
	}
</script>

<ul class="list-none flex flex-col gap-2">
	<DateRangeInput bind:startDate bind:endDate />
	<div class="form-control">
		<input
			type="text"
			placeholder="Filter by label"
			class="input input-bordered"
			bind:value={prefix}
		/>
	</div>
	<LoadingStatus items={$txs} label="transactions" />
	{#if $txs}
		<GroupedTransactionList txs={$txs} {handleChange} {handleDelete} />
	{/if}
</ul>
