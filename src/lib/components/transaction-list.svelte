<script lang="ts">
	import { getDbContext } from '$lib/context';
	import { endOfDay, format, startOfDay, subDays } from 'date-fns';
	import { liveQuery } from 'dexie';
	import GroupedTransactionList from './grouped-transaction-list.svelte';
	import DateRangeInput from './ui/date-range-input.svelte';
	import LoadingStatus from './ui/loading-status.svelte';
	import { searchLiveQuery } from '$lib/dexie/utils/transactions';

	const db = getDbContext();

	let startDate = $state(subDays(new Date(), 30));
	let endDate = $state(new Date());
	let prefix = $state('');

	let txs = $derived.by(() => {
		// noop just to make it reactive
		prefix;
		startDate;
		endDate;

		return searchLiveQuery({
			startDate,
			endDate,
			prefix
		});
	});
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
		<GroupedTransactionList txs={$txs} />
	{/if}
</ul>
