<script lang="ts">
	import { getDbContext } from '$lib/context';
	import { subDays } from 'date-fns';
	import { liveQuery } from 'dexie';
	import GroupedTransactionList from './grouped-transaction-list.svelte';
	import DateRangeInput from './ui/date-range-input.svelte';
	import LoadingStatus from './ui/loading-status.svelte';
	import { searchLiveQuery } from '$lib/dexie/utils/transactions';
	import PillMultiSelect from './ui/pill-multi-select.svelte';

	const db = getDbContext();

	let startDate = $state(subDays(new Date(), 30));
	let endDate = $state(new Date());
	let searchTerm = $state('');
	let selectedCategoryIds = $state<string[]>([]);

	const categories = $derived.by(() => {
		return liveQuery(() => db.category.toArray());
	});

	let txs = $derived.by(() => {
		// noop just to make it reactive
		searchTerm;
		startDate;
		endDate;
		selectedCategoryIds;

		return searchLiveQuery({
			startDate,
			endDate,
			searchTerm,
			categoryIds: selectedCategoryIds
		});
	});
</script>

<ul class="list-none flex flex-col gap-2">
	<DateRangeInput bind:startDate bind:endDate />
	<div class="form-control">
		<input
			type="text"
			placeholder="Search transactions..."
			class="input input-bordered"
			bind:value={searchTerm}
		/>
	</div>
	{#if $categories}
		<PillMultiSelect
			items={$categories}
			bind:selectedIds={selectedCategoryIds}
			displayProperty="label"
			valueProperty="id"
			label="Filter by categories"
		/>
	{/if}
	<LoadingStatus items={$txs} label="transactions" />
	{#if $txs}
		<GroupedTransactionList txs={$txs} />
	{/if}
</ul>
