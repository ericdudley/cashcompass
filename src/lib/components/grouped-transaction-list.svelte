<script lang="ts">
	import type { Transaction } from '$lib/dexie/models/transaction';
	import { formatAmount } from '$lib/format';
	import { format, parse } from 'date-fns';
	import TransactionListItem from './transaction-list-item.svelte';

	let { txs } = $props<{
		txs: Transaction[];
	}>();

	type Item = { key: string } & (
		| { type: 'yearHeader'; year: string; total: number }
		| { type: 'monthHeader'; month: string; total: number }
		| { type: 'dayHeader'; day: string; total: number }
		| { type: 'transaction'; transaction: Transaction }
	);

	let items: Item[] | null = $derived.by(() => {
		let lastYearStr = null;
		let lastMonthStr = null;
		let lastDayStr = null;

		let yearTotal = 0;
		let monthTotal = 0;
		let dayTotal = 0;

		let listItems: Item[] = [];
		let lastIsoStr = '';

		for (let i = 0; i < txs.length; i++) {
			let transaction = txs[i];

			let date = transaction.yyyyMMDd
				? parse(transaction.yyyyMMDd, 'yyyy-MM-dd', new Date())
				: new Date();
			let yearStr = format(date, 'yyyy');
			let monthStr = format(date, 'MMM');
			let dayStr = format(date, 'EEE, dd');
			let isoStr = format(date, 'yyyy-MM-dd');

			let itemsToAdd: Item[] = [];

			// Day change detected
			if (lastDayStr !== null && lastDayStr !== dayStr) {
				itemsToAdd.push({
					type: 'dayHeader',
					key: `day-${lastIsoStr}`,
					day: lastDayStr,
					total: dayTotal
				});
				dayTotal = 0; // Reset day total for the new day
			}

			// Month change detected
			if (lastMonthStr !== null && lastMonthStr !== monthStr) {
				itemsToAdd.push({
					type: 'monthHeader',
					key: `month-${lastIsoStr}`,
					month: lastMonthStr,
					total: monthTotal
				});
				monthTotal = 0; // Reset month total for the new month
			}

			// Year change detected
			if (lastYearStr !== null && lastYearStr !== yearStr) {
				itemsToAdd.push({
					type: 'yearHeader',
					key: `year-${lastIsoStr}`,
					year: lastYearStr,
					total: yearTotal
				});
				yearTotal = 0; // Reset year total for the new year
			}

			// Update date trackers
			lastDayStr = dayStr;
			lastMonthStr = monthStr;
			lastYearStr = yearStr;
			lastIsoStr = isoStr;

			// Accumulate totals
			dayTotal += transaction.amount;
			monthTotal += transaction.amount;
			yearTotal += transaction.amount;

			// Add the transaction
			itemsToAdd.push({
				type: 'transaction',
				key: `transaction-${transaction.id}`,
				transaction: transaction
			});

			listItems.push(...itemsToAdd);
		}

		// Push headers for the final date group
		if (lastDayStr && lastMonthStr && lastYearStr) {
			listItems.push({
				type: 'dayHeader',
				key: `day-${lastIsoStr}`,
				day: lastDayStr,
				total: dayTotal
			});
			listItems.push({
				type: 'monthHeader',
				key: `month-${lastIsoStr}`,
				month: lastMonthStr,
				total: monthTotal
			});
			listItems.push({
				type: 'yearHeader',
				key: `year-${lastIsoStr}`,
				year: lastYearStr,
				total: yearTotal
			});
		}

		// Reverse list for headers at the top
		listItems.reverse();

		return listItems;
	});
</script>

{#each items as item (item.key)}
	{#if item.type === 'yearHeader'}
		<li class="mb-1 opacity-80">
			<div class="flex items-center gap-1">
				<h2 class="text-xl font-extrabold">{item.year}</h2>
				<span class="text-sm italic opacity-70">{formatAmount(item.total)}</span>
			</div>
			<div class="w-full mt-1 h-0.5 bg-base-300"></div>
		</li>
	{:else if item.type === 'monthHeader'}
		<li class="mb-1 ml-1 opacity-80">
			<div class="flex items-center gap-1">
				<h2 class="text-lg font-bold">{item.month}</h2>
				<span class="text-sm italic opacity-70">{formatAmount(item.total)}</span>
			</div>
			<div class="mt-1 h-0.5 w-3/4 bg-base-300"></div>
		</li>
	{:else if item.type === 'dayHeader'}
		<li class="ml-2 opacity-80">
			<div class="flex items-center gap-1">
				<h2 class="text-md">{item.day}</h2>
				<span class="text-sm italic opacity-70">{formatAmount(item.total)}</span>
			</div>
			<div class="mt-1 h-0.5 w-1/2 bg-base-300"></div>
		</li>
	{:else if item.type === 'transaction'}
		<TransactionListItem transaction={item.transaction} />
	{/if}
{/each}
