<script lang="ts">
	import TrashIcon from 'virtual:icons/mdi/trash';
	import DisplayInput from './ui/display-input.svelte';
	import { liveQuery } from 'dexie';
	import { getDbContext } from '$lib/context';
	import TransactionIcon from './ui/icons/transaction-icon.svelte';
	import { formatAmount } from '$lib/format';
	import CategoryPill from './category-pill.svelte';
	import type { Transaction } from '$lib/dexie/models/transaction';
	import { parse, format } from 'date-fns';

	let { prefix }: { prefix: string } = $props();
	const db = getDbContext();

	let transactions = $derived.by(() => {
		// noop just to make it reactive
		prefix;

		return liveQuery(() =>
			db.tx
				.where('label')
				.startsWithIgnoreCase(prefix ?? '')
				.sortBy('yyyyMMDd')
		);
	});

	async function handleChange(id: string, label: string) {
		await db.tx.update(id, { label });
	}

	async function handleDelete(id: string) {
		if (!confirm('Are you sure you want to delete this transaction?')) return;

		await db.tx.delete(id);
	}

	let items: Array<
		| { type: 'yearHeader'; key: string; year: string; total: number }
		| { type: 'monthHeader'; key: string; month: string; total: number }
		| { type: 'dayHeader'; key: string; day: string; total: number }
		| { type: 'transaction'; key: string; transaction: Transaction }
	> = $derived.by(() => {
		if (!transactions || !$transactions) {
			return [];
		}

		let lastYearStr = null;
		let lastMonthStr = null;
		let lastDayStr = null;

		let lastYearTotal = 0;
		let lastMonthTotal = 0;
		let lastDayTotal = 0;

		let listItems = [];

		let lastIsoStr = '';

		for (let i = 0; i < $transactions.length; i++) {
			let transaction = $transactions[i];

			let date = transaction.yyyyMMDd
				? parse(transaction.yyyyMMDd, 'yyyy-MM-dd', new Date())
				: new Date();
			let yearStr = format(date, 'yyyy');
			let monthStr = format(date, 'MMM');
			let dayStr = format(date, 'EEE, dd');
			let isoStr = format(date, 'yyyy-MM-dd');

			let itemsToAdd = [];

			// When the day changes (and it's not the first transaction)
			if (lastDayStr !== null && lastDayStr !== dayStr) {
				// Push headers for the previous date
				itemsToAdd.push({
					type: 'dayHeader',
					key: `day-${lastIsoStr}`,
					day: lastDayStr,
					total: lastDayTotal
				});

				if (lastMonthStr !== monthStr) {
					itemsToAdd.push({
						type: 'monthHeader',
						key: `month-${lastIsoStr}`,
						month: lastMonthStr,
						total: lastMonthTotal
					});
				}

				if (lastYearStr !== yearStr) {
					itemsToAdd.push({
						type: 'yearHeader',
						key: `year-${lastIsoStr}`,
						year: lastYearStr,
						total: lastYearTotal
					});
				}

				// Reset totals for the new date
				lastDayTotal = 0;
				lastMonthTotal = 0;
				lastYearTotal = 0;
			}

			// Update the last date trackers
			lastDayStr = dayStr;
			lastMonthStr = monthStr;
			lastYearStr = yearStr;
			lastIsoStr = isoStr;

			// Accumulate totals
			lastDayTotal += transaction.amount;
			lastMonthTotal += transaction.amount;
			lastYearTotal += transaction.amount;

			// Add the transaction
			itemsToAdd.push({
				type: 'transaction',
				key: `transaction-${transaction.id}`,
				transaction: transaction
			});

			listItems.push(...itemsToAdd);
		}

		// After processing all transactions, push headers for the last date group
		if (lastDayStr !== null) {
			listItems.push({
				type: 'dayHeader',
				key: `day-${lastIsoStr}`,
				day: lastDayStr,
				total: lastDayTotal
			});
			listItems.push({
				type: 'monthHeader',
				key: `month-${lastIsoStr}`,
				month: lastMonthStr,
				total: lastMonthTotal
			});
			listItems.push({
				type: 'yearHeader',
				key: `year-${lastIsoStr}`,
				year: lastYearStr,
				total: lastYearTotal
			});
		}

		// Reverse the list to have headers at the top
		listItems.reverse();

		return listItems;
	});
</script>

<ul class="list-none flex flex-col gap-2">
	{#if items}
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
				<li class="flex items-center justify-between">
					<span class="flex items-center text-sm font-medium me-3 gap-1">
						<TransactionIcon />
						<span>
							{formatAmount(item.transaction.amount)}
						</span>
						<DisplayInput
							value={item.transaction.label ?? ''}
							onSave={(value) => handleChange(item.transaction.id, value)}
						/>
					</span>
					<div class="flex gap-1 items-center">
						{#if item.transaction.category}
							<CategoryPill label={item.transaction.category.label} />
						{/if}
						<button
							class="btn btn-square btn-sm btn-error btn-ghost"
							onclick={() => handleDelete(item.transaction.id)}
						>
							<TrashIcon />
						</button>
					</div>
				</li>
			{/if}
		{/each}
	{/if}
</ul>
