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
