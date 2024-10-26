<script lang="ts">
	import TrashIcon from 'virtual:icons/mdi/trash';
	import DisplayInput from './ui/display-input.svelte';
	import { liveQuery } from 'dexie';
	import { getDbContext } from '$lib/context';
	import TransactionIcon from './ui/icons/transaction-icon.svelte';
	import { formatAmount } from '$lib/format';
	import CategoryPill from './category-pill.svelte';
	import type { Transaction } from '$lib/dexie/models/transaction';

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

		let lastYearTotal = 0;
		let lastYearStr = '';
		let lastMonthTotal = 0;
		let lastMonthStr = '';
		let lastDayTotal = 0;
		let lastDayStr = '';

		// Prepare the transactions array by adding a dummy transaction at the end
		let transactionsWithDummy = [
			...$transactions,
			{ unixMs: 0, amount: 0, label: 'DUMMY', id: 'DUMMY', yyyyMMDd: '' }
		];

		let listItems = [];

		for (let i = 0; i < transactionsWithDummy.length; i++) {
			let transaction = transactionsWithDummy[i];

			let date = new Date(transaction.unixMs);
			let isoStr = date.toISOString();
			let yearStr = date.getFullYear().toString();
			let monthStr = date.toLocaleString('default', { month: 'short' });
			let dayStr = date.toLocaleString('default', { weekday: 'short', day: '2-digit' });

			// Initialize lastYearStr, lastMonthStr, lastDayStr
			if (!lastYearStr) lastYearStr = yearStr;
			if (!lastMonthStr) lastMonthStr = monthStr;
			if (!lastDayStr) lastDayStr = dayStr;

			let itemsToAdd: Array<
				| { type: 'yearHeader'; key: string; year: string; total: number }
				| { type: 'monthHeader'; key: string; month: string; total: number }
				| { type: 'dayHeader'; key: string; day: string; total: number }
				| { type: 'transaction'; key: string; transaction: Transaction }
			> = [];

			if (lastYearStr !== yearStr || transaction.id === 'DUMMY') {
				itemsToAdd.push({
					type: 'yearHeader',
					key: `year-${isoStr}`,
					year: lastYearStr,
					total: lastYearTotal
				});
				lastYearTotal = 0;
				lastYearStr = yearStr;
			}

			if (lastMonthStr !== monthStr || transaction.id === 'DUMMY') {
				itemsToAdd.push({
					type: 'monthHeader',
					key: `month-${isoStr}`,
					month: lastMonthStr,
					total: lastMonthTotal
				});
				lastMonthTotal = 0;
				lastMonthStr = monthStr;
			}

			if (lastDayStr !== dayStr || transaction.id === 'DUMMY') {
				itemsToAdd.push({
					type: 'dayHeader',
					key: `day-${isoStr}`,
					day: lastDayStr,
					total: lastDayTotal
				});
				lastDayTotal = 0;
				lastDayStr = dayStr;
			}

			lastYearTotal += transaction.amount;
			lastMonthTotal += transaction.amount;
			lastDayTotal += transaction.amount;

			if (transaction.id !== 'DUMMY') {
				itemsToAdd.push({
					type: 'transaction',
					key: `transaction-${transaction.id}`,
					transaction: transaction
				});
			}

			listItems.push(...itemsToAdd);
		}

		return listItems.reverse();
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
					<span>
						{new Date(item.transaction.unixMs).toLocaleDateString()}
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
