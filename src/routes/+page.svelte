<script lang="ts">
	import { getDbContext } from '$lib/context';
	import {
		getAverageMonthly,
		getCategoryMonthlyTotals,
		getNetWorthByMonth,
		getPercentageDiffFromLastMonth,
		getTotalThisMonth
	} from '$lib/dexie/utils/transactions';
	import { formatAmount } from '$lib/format';
	import { format, sub } from 'date-fns';

	import DateRangeInput from '$lib/components/ui/date-range-input.svelte';
	import { liveQuery } from 'dexie';
	import { startOfMonth } from 'date-fns/startOfMonth';

	const db = getDbContext();

	// Initialize state variables
	let startDate = $state(
		startOfMonth(
			sub(new Date(), {
				months: 2
			})
		)
	);
	let endDate = $state(new Date());

	// Fetch transactions based on date range
	const debitTxs = $derived.by(() => {
		// Make the derived store reactive to startDate and endDate
		startDate;
		endDate;

		// Create a store from the liveQuery observable
		return liveQuery(() =>
			db.tx
				.where('yyyyMMDd')
				.between(format(startDate, 'yyyy-MM-dd'), format(endDate, 'yyyy-MM-dd'), true, true)
				.filter((tx) => tx.account?.accountType === 'expenses')
				.filter((tx) => tx.amount < 0)
				.sortBy('yyyyMMDd')
		);
	});

	// Await the transactions store

	// Calculate derived values
	const totalThisMonth = $derived(getTotalThisMonth($debitTxs ?? []));
	const percentageDiffFromLastMonth = $derived(getPercentageDiffFromLastMonth($debitTxs ?? []));
	const averageMonthly = $derived(getAverageMonthly($debitTxs ?? []));
	const categoryMonthlyTotals = $derived(getCategoryMonthlyTotals($debitTxs ?? []));

	// We need all txs in order to correctly calculate balances (until optimization for this is implemented)
	const netWorthTxs = $derived.by(() =>
		liveQuery(() =>
			db.tx.filter((tx) => tx.account?.accountType === 'net_worth').sortBy('yyyyMMDd')
		)
	);
	const netWorthDataValue = $derived.by(() => getNetWorthByMonth($netWorthTxs ?? []));

	// Prepare months, categories, and table data using $computed
	const months = $derived.by(() => categoryMonthlyTotals?.months || []);
	// FIXME Fix this type
	const tableData: any = $derived.by(() => {
		if (!categoryMonthlyTotals?.data) return [];

		const data = Object.entries(categoryMonthlyTotals.data).map(([category, data]) => ({
			category,
			...data
		}));

		// Add a totals row for the totals per month
		const totalsRow = {
			category: 'Total',
			...categoryMonthlyTotals.totalsPerMonth,
			Total: categoryMonthlyTotals.totalOverall,
			Average: 0
		};
		data.push(totalsRow);

		return data;
	});
</script>

<DateRangeInput bind:startDate bind:endDate />

<div class="stats shadow my-4 stats-vertical md:stats-horizontal">
	<div class="stat">
		<div class="stat-title">This Month</div>
		<div class="stat-value">{formatAmount(totalThisMonth ?? 0)}</div>
		<div class="stat-desc">
			{Math.round(percentageDiffFromLastMonth)}% {percentageDiffFromLastMonth > 0 ? 'more' : 'less'}
			than last month
		</div>
	</div>
	<div class="stat">
		<div class="stat-title">Average Monthly</div>
		<div class="stat-value">{formatAmount(averageMonthly ?? 0)}</div>
		<div class="stat-desc">Excluding the current month</div>
	</div>
</div>

<h2 class="text-2xl font-bold my-4">Expenses</h2>
<div class="overflow-x-auto">
	<table class="table table-zebra w-full">
		<thead>
			<tr>
				<th class="bg-base-200 sticky left-0 z-10">Category</th>
				{#each months as month}
					<th>{month}</th>
				{/each}
				<th>Total</th>
				<th>Average</th>
			</tr>
		</thead>
		<tbody>
			{#each tableData as row}
				<tr>
					<td class="bg-base-200 sticky left-0 z-10 font-bold">{row.category}</td>
					{#each months as month}
						<td>{formatAmount(row[month] ?? 0)}</td>
					{/each}
					<td>{formatAmount(row.Total ?? 0)}</td>
					<td>{row.Average !== '' ? formatAmount(row.Average ?? 0) : ''}</td>
				</tr>
			{/each}
		</tbody>
	</table>
</div>

{#if netWorthDataValue}
	<h2 class="text-2xl font-bold my-4">Net Worth</h2>
	<div class="overflow-x-auto">
		<table class="table table-zebra w-full">
			<thead>
				<tr>
					<th class="bg-base-200 sticky left-0 z-10">Account</th>
					{#each netWorthDataValue.months as month}
						<th>{month}</th>
					{/each}
				</tr>
			</thead>
			<tbody>
				{#each Object.entries(netWorthDataValue.data) as [accountLabel, balances]}
					<tr>
						<td class="bg-base-200 sticky left-0 z-10 font-bold">{accountLabel}</td>
						{#each netWorthDataValue.months as month}
							<td>{formatAmount(balances[month] || 0)}</td>
						{/each}
					</tr>
				{/each}
			</tbody>
		</table>
	</div>
{/if}
